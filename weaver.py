import time
from typing import Dict, List, Optional, Tuple
from web3 import Web3
from datetime import datetime
from config import Config
from bureau_core import audit_signal

# =====================================================
# 🏛️ PADI WEAVER v2.0 — NAIROBI NODE-01
# Phase Two: Multi-Network Nervous System with Batch Signal Ingestion
# Supports: OP Mainnet, OP Sepolia, ETH Mainnet, ETH Sepolia
# =====================================================

class Weaver:
    """
    The Weaver synchronizes external signals with live blockchain context
    across multiple networks (OP Mainnet, OP Sepolia, ETH Mainnet, ETH Sepolia)
    and triggers the SHACL-enforced Audit in batch or individually.
    
    Multi-network capable with automatic network routing and context extraction.
    """

    def __init__(self):
        """Initialize Weaver with multi-network support."""
        # 1. Validate configuration
        if not Config.validate():
            raise ConnectionError("❌ Weaver aborted: Invalid Configuration.")
        
        # 2. Initialize multi-network connections
        self.node_id = Config.NODE_ID
        self.w3_connections: Dict[str, Web3] = {}
        self._initialize_networks()

    def _initialize_networks(self):
        """
        Initialize Web3 connections for all configured networks.
        Logs warnings for networks without RPC URLs.
        """
        configured = Config.get_configured_networks()
        
        if not configured:
            raise ConnectionError(
                f"❌ {self.node_id}: No networks configured. "
                "At least one network must be configured in config.py"
            )
        
        for network_type, config in configured.items():
            try:
                w3 = Web3(Web3.HTTPProvider(config["rpc_url"]))
                if w3.is_connected():
                    self.w3_connections[network_type] = w3
                    print(f"🚀 {self.node_id}: Connected to {config['name']} (Chain ID: {config['chain_id']})")
                else:
                    print(f"⚠️ {self.node_id}: Failed to connect to {config['name']} (RPC URL: {config['rpc_url']})")
            except Exception as e:
                print(f"❌ {self.node_id}: Error connecting to {config['name']}: {e}")
        
        if not self.w3_connections:
            raise ConnectionError(f"❌ {self.node_id}: No networks connected. Weaver cannot process signals.")

    # ---------------------------
    # Live network context
    # ---------------------------
    def get_live_context(self, network_type: str) -> Optional[Dict[str, any]]:
        """
        Fetch latest block and gas price from specified network.
        
        Args:
            network_type: Network type ("op-mainnet", "op-sepolia", "eth-mainnet", "eth-sepolia", "base-l2")
        
        Returns:
            Dictionary with block number, gas price, and timestamp, or None if error
        """
        # Validate network configuration
        if network_type not in self.w3_connections:
            print(f"❌ Network {network_type} not connected. Cannot fetch context.")
            return None
        
        w3 = self.w3_connections[network_type]
        
        try:
            latest_block = w3.eth.get_block('latest')
            gas_price = w3.from_wei(w3.eth.gas_price, 'gwei')
            return {
                "block_number": latest_block['number'],
                "gas_price": float(gas_price),
                "timestamp": datetime.fromtimestamp(latest_block['timestamp']).isoformat(),
                "network_type": network_type
            }
        except Exception as e:
            print(f"📡 RPC Sync Error on {network_type}: {e}")
            return None

    # ---------------------------
    # Process a single signal
    # ---------------------------
    def process_signal(
        self,
        raw_data: Dict[str, any],
        network_type: Optional[str] = None
    ) -> Optional:
        """
        Process a single signal with multi-network support.
        
        Args:
            raw_data: Signal data dictionary with required fields
            network_type: Network type (optional, extracted from raw_data if not provided)
        
        Returns:
            RDF Graph if signal promoted to ExecutableFact, None otherwise
        """
        # Extract or infer network type
        if network_type is None:
            network_type = raw_data.get("network_type", Config.DEFAULT_NETWORK_TYPE)
        
        # Validate network type
        if network_type not in self.w3_connections:
            print(f"❌ Network {network_type} not connected. Signal rejected: {raw_data.get('label', 'Unknown')}")
            return None
        
        # Get network-specific context
        ctx = self.get_live_context(network_type)
        if not ctx:
            print(f"🛡️ Safety Lock: Signal rejected due to Infrastructure Desync on {network_type}.")
            return None

        print(f"\n--- 🧵 Weaving Signal: {raw_data.get('label', 'Unknown')} ({network_type}) ---")
        
        # Prepare network-specific parameters
        network_config = Config.get_network_config(network_type)
        chain_id = network_config["chain_id"]
        source_provider = raw_data.get("source_provider", network_config["rpc_url"])
        
        # Extract verification metadata
        verification_confidence = raw_data.get("verification_confidence")
        verification_timestamp = raw_data.get("verification_timestamp")
        verification_match = raw_data.get("verification_match")
        
        # Extract cross-network verification parameters
        primary_network = raw_data.get("primary_network", network_type)
        fallback_network = raw_data.get("fallback_network")
        cross_network_verification = raw_data.get("cross_network_verification", Config.DEFAULT_CROSS_NETWORK_VERIFICATION)
        
        graph, conforms, status, report = audit_signal(
            name=raw_data.get("label", f"SIG-{int(time.time())}"),
            confidence=raw_data.get("confidence", 0.0),
            sources=raw_data.get("sources", []),
            target_address=raw_data.get("target", "0x000"),
            action_type=raw_data.get("action", "OBSERVE"),
            signal_id=raw_data.get("uid", f"SIG-{int(time.time())}"),
            # NEW: Network context parameters
            network_type=network_type,
            chain_id=chain_id,
            source_provider=source_provider,
            # NEW: Verification metadata parameters
            verification_confidence=verification_confidence,
            verification_timestamp=verification_timestamp,
            verification_match=verification_match,
            # NEW: Cross-network verification parameters
            primary_network=primary_network,
            fallback_network=fallback_network,
            cross_network_verification=cross_network_verification,
            # Existing parameters
            block_number=ctx["block_number"],
            gas_price_gwei=ctx["gas_price"],
            observed_at=ctx["timestamp"],
            is_validated=False
        )

        # Reporting
        if conforms:
            print(f"✅ DETERMINISTIC: Signal promoted to ExecutableFact.")
            print(f"📍 Target: {raw_data.get('target')} | Network: {network_type} | Block: {ctx['block_number']}")
        else:
            print(f"❌ PROBABILISTIC: Signal Blocked by Sentinel.")
            if Config.DEBUG:
                print(f"Reasoning:\n{report}")

        return graph if conforms else None

    # ---------------------------
    # Batch signal processing
    # ---------------------------
    def process_batch(
        self,
        signals: List[Dict[str, any]]
    ) -> List:
        """
        Processes multiple signals in a deterministic batch.
        Each signal is validated and promoted individually.
        Signals can be from different networks.
        
        Args:
            signals: List of signal data dictionaries
        
        Returns:
            List of RDF graphs for promoted ExecutableFacts
        """
        print(f"\n--- 🔄 Weaver: Processing batch of {len(signals)} signals ---")
        results = []
        
        # Group signals by network for efficient processing
        signals_by_network: Dict[str, List[Dict[str, any]]] = {}
        for sig in signals:
            network_type = sig.get("network_type", Config.DEFAULT_NETWORK_TYPE)
            if network_type not in signals_by_network:
                signals_by_network[network_type] = []
            signals_by_network[network_type].append(sig)
        
        # Process signals by network
        for network_type, network_signals in signals_by_network.items():
            print(f"\n--- 🔄 Processing {len(network_signals)} signals on {network_type} ---")
            for sig in network_signals:
                graph = self.process_signal(sig, network_type)
                if graph:
                    results.append(graph)
        
        promoted_count = len(results)
        total_count = len(signals)
        print(f"\n✅ Batch complete: {promoted_count}/{total_count} signals promoted.")
        
        # Display breakdown by network
        for network_type, network_signals in signals_by_network.items():
            network_promoted = sum(
                1 for sig in network_signals
                if self._signal_was_promoted(sig, results)
            )
            print(f"   {network_type}: {network_promoted}/{len(network_signals)} promoted")
        
        return results

    def _signal_was_promoted(
        self,
        signal: Dict[str, any],
        promoted_graphs: List
    ) -> bool:
        """
        Check if a signal was promoted to ExecutableFact.
        
        Args:
            signal: Signal data dictionary
            promoted_graphs: List of promoted RDF graphs
        
        Returns:
            True if signal was promoted, False otherwise
        """
        signal_id = signal.get("uid")
        if not signal_id:
            return False
        
        # Check if any promoted graph contains this signal ID
        for graph in promoted_graphs:
            from rdflib import Namespace
            EX = Namespace("http://padi.u/schema#")
            signal_id_values = graph.value(EX[signal_id.split("-")[0] if "-" in signal_id else signal_id], EX.hasSignalID)
            if signal_id_values and str(signal_id_values) == signal_id:
                return True
        
        return False
    
    # ---------------------------
    # Network management methods
    # ---------------------------
    def get_connected_networks(self) -> List[str]:
        """
        Get list of connected network types.
        
        Returns:
            List of connected network type strings
        """
        return list(self.w3_connections.keys())

    def get_network_status(self) -> Dict[str, Dict[str, str]]:
        """
        Get connection status for all configured networks.
        
        Returns:
            Dictionary mapping network types to status information
        """
        status = {}
        configured = Config.get_configured_networks()
        
        for network_type, config in configured.items():
            w3 = self.w3_connections.get(network_type)
            status[network_type] = {
                "name": config["name"],
                "chain_id": config["chain_id"],
                "connected": w3 is not None,
                "rpc_url": config["rpc_url"]
            }
        
        return status


# ---------------------------
# Example / Standalone Test
# ---------------------------
if __name__ == "__main__":
    print("--- 🏛️ PADI WEAVER: NAIROBI NODE-01 STANDALONE TEST ---")
    print()
    
    try:
        weaver = Weaver()
        
        # Display network status
        print("=== Network Status ===")
        status = weaver.get_network_status()
        for network, info in status.items():
            conn_status = "✅ Connected" if info["connected"] else "❌ Disconnected"
            print(f"{info['name']} (Chain ID {info['chain_id']}): {conn_status}")
        print()

        # Example batch of multi-network signals
        mock_batch = [
            # OP Mainnet Signal (Should pass)
            {
                "label": "Alpha_Arb_OP_001",
                "confidence": 1.0,
                "sources": ["Pyth-OP", "Chainlink-OP", "Uniswap_Events-OP"],
                "target": "0x4752ba5DBc23f44D620376279d4b37A730947593",
                "action": "ARBITRAGE",
                "uid": "OP-TX-001",
                # NEW: OP Mainnet network context
                "network_type": "op-mainnet",
                "source_provider": "Alchemy-OP-Mainnet",
                "verification_confidence": [1.0, 1.0, 1.0],
                "verification_timestamp": ["2026-03-26T01:00:00Z", "2026-03-26T01:00:01Z", "2026-03-26T01:00:02Z"],
                "verification_match": [True, True, True],
                "primary_network": "op-mainnet",
                "fallback_network": "eth-mainnet",
                "cross_network_verification": True
            },
            # Ethereum Mainnet Signal (Should pass)
            {
                "label": "Beta_Arb_ETH_001",
                "confidence": 1.0,
                "sources": ["Pyth-ETH", "Chainlink-ETH", "Uniswap_Events-ETH"],
                "target": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                "action": "ARBITRAGE",
                "uid": "ETH-TX-001",
                # NEW: Ethereum Mainnet network context
                "network_type": "eth-mainnet",
                "source_provider": "Alchemy-ETH-Mainnet",
                "verification_confidence": [1.0, 1.0, 1.0],
                "verification_timestamp": ["2026-03-26T01:00:03Z", "2026-03-26T01:00:04Z", "2026-03-26T01:00:05Z"],
                "verification_match": [True, True, True],
                "primary_network": "eth-mainnet",
                "cross_network_verification": True
            },
            # Probabilistic Signal (Should fail)
            {
                "label": "Gamma_Arb_002",
                "confidence": 0.9,  # Should fail 1003 Rule
                "sources": ["Pyth"],  # Only 1 source (should be 3)
                "target": "0x9999ba5DBc23f44D620376279d4b37A730947999",
                "action": "SWAP",
                "uid": "PROB-TX-001",
                # NEW: OP Mainnet network context (but will fail 1003 rule)
                "network_type": "op-mainnet",
                "source_provider": "Alchemy-OP-Mainnet"
            }
        ]

        weaver.process_batch(mock_batch)
        
        print()
        print("=== Test Complete ===")
        
    except ConnectionError as e:
        print(e)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
