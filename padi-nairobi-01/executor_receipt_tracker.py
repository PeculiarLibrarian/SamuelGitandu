#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🏛️ PADI EXECUTOR v5.3 — Receipt Tracker
==================================================

Component:
- ReceiptTracker: Transaction receipt monitoring with intelligent re-broadcast

Features:
- Background monitoring with configurable intervals
- Stuck transaction detection and re-broadcast with gas escalation
- Full receipt verification and metric tracking
- Thread-safe pending transaction management

Version: 5.3
Node: Nairobi-01
Timestamp: 2026-03-26 [EAT]
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from web3 import Web3
from web3.exceptions import TimeExhausted, TransactionNotFound
import logging

logger = logging.getLogger("PADI-RECEIPT-TRACKER")


# =====================================================
# Receipt Tracker
# =====================================================

class ReceiptTracker:
    """
    Enhanced transaction receipt tracking with intelligent re-broadcast logic.
    
    Features:
    - Background monitoring with configurable intervals
    - Stuck transaction detection and re-broadcast with escalation
    - Full receipt verification and metric tracking
    - Thread-safe pending transaction management
    
    Args:
        executor_w3_connections: Dictionary of Web3 connections by network name
        executor_private_key: Private key for re-signing transactions
        executor_address: Wallet address for the executor
        logger: Logger instance
    """
    
    def __init__(
        self,
        executor_w3_connections: Dict[str, Web3],
        executor_private_key: str,
        executor_address: str,
        logger: logging.Logger
    ):
        self.w3_connections = executor_w3_connections
        self.private_key = executor_private_key
        self.address = executor_address
        self.logger = logger
        
        # Pending transaction tracking
        self.pending_txs: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
        # Monitoring statistics
        self.stats = {
            "total_monitored": 0,
            "total_confirmed": 0,
            "total_failed": 0,
            "total_rebroadcasts": 0,
            "total_abandoned": 0
        }
        
        # Monitor lifecycle
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Configuration (can be overridden)
        self.config = {
            "check_interval_seconds": 30,
            "stuck_threshold_minutes": 5,
            "max_rebroadcast_attempts": 3,
            "gas_escalation_percent": 20,
            "abandon_threshold_minutes": 15
        }
    
    def set_config(self, config: Dict[str, Any]):
        """
        Update configuration.
        
        Args:
            config: Dictionary of configuration overrides
        """
        self.config.update(config)
        logger.info(f"🔍 ReceiptTracker config updated: {self.config}")
    
    def add_pending(
        self,
        tx_hash: str,
        network_name: str,
        tx_data: Dict[str, Any],
        gas_used: int = 0,
        l1_fee: int = 0
    ):
        """
        Add a pending transaction to track.
        
        Args:
            tx_hash: Transaction hash (hex string)
            network_name: Network identifier
            tx_data: Full transaction dictionary
            gas_used: Estimated gas used
            l1_fee: L1 data fee (if applicable)
        """
        with self.lock:
            self.pending_txs[tx_hash] = {
                "network": network_name,
                "tx_hash": tx_hash,
                "submitted_at": datetime.now(),
                "last_attempt_at": datetime.now(),
                "attempts": 1,
                "gas_history": [],
                "data": tx_data,
                "gas_used": gas_used,
                "l1_fee": l1_fee,
                "status": "pending"  # pending, confirmed, failed, abandoned
            }
            self.stats["total_monitored"] += 1
        
        self.logger.info(f"🔍 Tracking transaction: {tx_hash} on {network_name}")

    def remove_pending(self, tx_hash: str, reason: str = ""):
        """
        Remove transaction from pending tracking.
        
        Args:
            tx_hash: Transaction hash to remove
            reason: Reason for removal (for logging)
        """
        with self.lock:
            if tx_hash in self.pending_txs:
                self.pending_txs.pop(tx_hash)
                if reason:
                    self.logger.info(f"🔍 Removed {tx_hash}: {reason}")

    def get_receipt(
        self,
        tx_hash: str,
        timeout: int = 120,
        poll_interval: float = 1.0
    ) -> Optional[Dict[str, Any]]:
        """
        Synchronously wait for transaction receipt.
        
        Args:
            tx_hash: Transaction hash
            timeout: Timeout in seconds
            poll_interval: Poll interval in seconds
        
        Returns:
            Receipt dict or None if timeout
        """
        with self.lock:
            pending = self.pending_txs.get(tx_hash)
            network_name = pending["network"] if pending else None
        
        if not network_name:
            return None
        
        w3 = self.w3_connections.get(network_name)
        if not w3:
            return None
        
        try:
            receipt = w3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=timeout,
                poll_latency=poll_interval
            )
            
            status = "success" if receipt['status'] == 1 else "failed"
            
            with self.lock:
                if status == "success":
                    self.stats["total_confirmed"] += 1
                else:
                    self.stats["total_failed"] += 1
            
            return {
                "status": status,
                "block_number": receipt['blockNumber'],
                "gas_used": receipt['gasUsed'],
                "effective_gas_price": receipt.get('effectiveGasPrice', 0),
                "tx_hash": tx_hash,
                "network": network_name,
                "timestamp": datetime.now().isoformat()
            }
        except TimeExhausted:
            self.logger.warning(f"⏱️ Transaction receipt timeout for {tx_hash}")
            return None
        except TransactionNotFound:
            self.logger.warning(f"🔍 Transaction not found for {tx_hash}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error getting receipt for {tx_hash}: {e}")
            return None

    def start_monitor(self, check_interval: Optional[int] = None):
        """
        Start background monitoring thread.
        
        Args:
            check_interval: Custom check interval in seconds
        """
        if self._running:
            self.logger.warning("🔍 Monitor already running")
            return
        
        self._running = True
        if check_interval:
            self.config["check_interval_seconds"] = check_interval
        
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ReceiptTrackerMonitor"
        )
        self._monitor_thread.start()
        self.logger.info(
            f"🔍 Receipt monitoring started: {self.config['check_interval_seconds']}s interval"
        )

    def stop_monitor(self, wait_for_completion: bool = True):
        """
        Stop background monitoring thread.
        
        Args:
            wait_for_completion: Wait for monitor thread to finish
        """
        self._running = False
        
        if self._monitor_thread and wait_for_completion:
            self._monitor_thread.join(timeout=10)
            if self._monitor_thread.is_alive():
                self.logger.warning("🔍 Monitor thread did not stop gracefully")
        
        self.logger.info("🔍 Receipt monitoring stopped")

    def _monitor_loop(self):
        """Background monitoring loop for pending transactions."""
        while self._running:
            try:
                self._check_pending_transactions()
            except Exception as e:
                self.logger.error(f"❌ Monitor loop error: {e}")
            
            time.sleep(self.config["check_interval_seconds"])

    def _check_pending_transactions(self):
        """Check all pending transactions and handle stuck ones."""
        check_cutoff_stuck = datetime.now() - timedelta(
            minutes=self.config["stuck_threshold_minutes"]
        )
        check_cutoff_abandon = datetime.now() - timedelta(
            minutes=self.config["abandon_threshold_minutes"]
        )
        
        with self.lock:
            pending_items = list(self.pending_txs.items())
        
        for tx_hash, tx_info in pending_items:
            submitted_at = tx_info["submitted_at"]
            network_name = tx_info["network"]
            tx_data = tx_info.get("data", {})
            
            w3 = self.w3_connections.get(network_name)
            if not w3:
                continue
            
            try:
                receipt = w3.eth.get_transaction_receipt(tx_hash)
                
                if receipt:
                    status = "confirmed" if receipt['status'] == 1 else "failed"
                    self._mark_finished(tx_hash, status, receipt)
                    self.logger.info(
                        f"✅ Transaction {tx_hash} {status} at block "
                        f"{receipt['blockNumber']} (Gas: {receipt['gasUsed']})"
                    )
                    continue
            except Exception as e:
                self.logger.error(f"❌ Error checking receipt for {tx_hash}: {e}")
                continue
            
            if submitted_at < check_cutoff_abandon:
                self._mark_abandoned(tx_hash)
                self.logger.error(
                    f"❌ Transaction {tx_hash} ABANDONED after "
                    f"{self.config['abandon_threshold_minutes']} minutes"
                )
                continue
            
            if submitted_at < check_cutoff_stuck:
                self._handle_stuck_transaction(tx_hash, tx_info, w3)

    def _mark_finished(self, tx_hash: str, status: str, receipt: Optional[Dict] = None):
        """Mark a transaction as finished."""
        with self.lock:
            if tx_hash in self.pending_txs:
                self.pending_txs[tx_hash]["status"] = status
                self.pending_txs[tx_hash]["finished_at"] = datetime.now()
                if receipt:
                    self.pending_txs[tx_hash]["receipt"] = {
                        "block_number": receipt['blockNumber'],
                        "gas_used": receipt['gasUsed'],
                        "effective_gas_price": receipt.get('effectiveGasPrice', 0)
                    }
                    if 'gas_used' in receipt:
                        self.pending_txs[tx_hash]["gas_history"].append(
                            {
                                "attempt": self.pending_txs[tx_hash]["attempts"],
                                "gas_used": int(receipt['gasUsed']),
                                "timestamp": datetime.now().isoformat()
                            }
                        )

    def _mark_abandoned(self, tx_hash: str):
        """Mark a transaction as abandoned."""
        with self.lock:
            if tx_hash in self.pending_txs:
                self.pending_txs[tx_hash]["status"] = "abandoned"
                self.pending_txs[tx_hash]["finished_at"] = datetime.now()
                self.pending_txs.pop(tx_hash)
                self.stats["total_abandoned"] += 1

    def _handle_stuck_transaction(
        self,
        tx_hash: str,
        tx_info: Dict[str, Any],
        w3: Web3
    ):
        """Handle a stuck transaction with intelligent re-broadcast logic."""
        attempts = tx_info["attempts"]
        max_attempts = self.config["max_rebroadcast_attempts"]
        
        if attempts >= max_attempts:
            self.logger.error(
                f"❌ Transaction {tx_hash} reached max re-broadcast attempts "
                f"({max_attempts}). Manual review required."
            )
            return
        
        self._rebroadcast_transaction(tx_hash, tx_info, w3, attempts)

    def _rebroadcast_transaction(
        self,
        tx_hash: str,
        tx_info: Dict[str, Any],
        w3: Web3,
        attempt: int
    ):
        """
        Re-broadcast transaction with escalated gas price.
        
        Strategy:
        - First re-broadcast: Same gas, just re-send
        - Subsequent broadcasts: Increase gas by percentage
        - Always ensure maxFeePerGas covers current base fee
        """
        self.logger.info(
            f"🔄 Re-broadcasting transaction {tx_hash} "
            f"(attempt {attempt + 1}/{self.config['max_rebroadcast_attempts']})"
        )
        
        try:
            latest_block = w3.eth.get_block('latest')
            base_fee = latest_block.get('baseFeePerGas', 0)
            current_max_fee = tx_info["data"].get("maxFeePerGas", base_fee * 2)
            current_priority_fee = tx_info["data"].get("maxPriorityFeePerGas", Web3.to_wei(1, 'gwei'))
            
            if attempt > 0:
                escalation_percent = self.config["gas_escalation_percent"]
                escalation_multiplier = 1 + (escalation_percent / 100)
                
                new_max_fee = int(current_max_fee * escalation_multiplier)
                new_priority_fee = int(current_priority_fee * escalation_multiplier)
                
                min_max_fee = int((base_fee * 2) + new_priority_fee)
                final_max_fee = max(new_max_fee, min_max_fee)
                
                tx_info["data"]["maxFeePerGas"] = final_max_fee
                tx_info["data"]["maxPriorityFeePerGas"] = new_priority_fee
                
                self.logger.info(
                    f"⛽ Gas escalated: {Web3.from_wei(current_max_fee, 'gwei'):.2f} → "
                    f"{Web3.from_wei(final_max_fee, 'gwei'):.2f} Gwei"
                )
            
            signed_tx = w3.eth.account.sign_transaction(
                tx_info["data"],
                self.private_key
            )
            
            new_tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction).hex()
            
            with self.lock:
                if tx_hash in self.pending_txs:
                    self.pending_txs[tx_hash]["attempts"] += 1
                    self.pending_txs[tx_hash]["last_attempt_at"] = datetime.now()
                    if "gas_history" not in self.pending_txs[tx_hash]:
                        self.pending_txs[tx_hash]["gas_history"] = []
                    self.pending_txs[tx_hash]["gas_history"].append({
                        "attempt": self.pending_txs[tx_hash]["attempts"],
                        "gas_price": float(Web3.from_wei(
                            tx_info["data"].get("maxFeePerGas", 0),
                            'gwei'
                        )),
                        "timestamp": datetime.now().isoformat()
                    })
            
            self.stats["total_rebroadcasts"] += 1
            
            self.logger.info(
                f"✅ Re-broadcast complete: {new_tx_hash} "
                f"(Attempt {self.pending_txs[tx_hash]['attempts']})"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Re-broadcast failed for {tx_hash}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get monitoring statistics.
        
        Returns:
            Dictionary of statistics
        """
        with self.lock:
            pending_count = len(self.pending_txs)
            pending_by_network = {}
            
            for tx_info in self.pending_txs.values():
                network = tx_info["network"]
                pending_by_network[network] = pending_by_network.get(network, 0) + 1
        
        return {
            **self.stats,
            "currently_pending": pending_count,
            "pending_by_network": pending_by_network,
            "monitor_running": self._running,
            "config": self.config
        }
