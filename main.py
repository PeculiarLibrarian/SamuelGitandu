import time
import signal
import logging
import threading
from typing import Dict, Optional
from config import Config
from weaver import Weaver
from executor import Executor

# =====================================================
# 🏛️ PADI BUREAU v2.0 — NAIROBI NODE-01
# main.py — Multi-Network Production Entry Point / Process Manager
# Supports: OP Mainnet, OP Sepolia, ETH Mainnet, ETH Sepolia
# =====================================================

# ---------------------------
# Logging Setup
# ---------------------------
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PADI-MAIN")

# ---------------------------
# Graceful Shutdown
# ---------------------------
shutdown_event = threading.Event()

def shutdown_handler(sig, frame):
    """Handle graceful shutdown on SIGINT."""
    logger.info("🛑 SIGINT received. Shutting down Nairobi Node gracefully...")
    shutdown_event.set()

signal.signal(signal.SIGINT, shutdown_handler)

# ---------------------------
# Node Bootstrap
# ---------------------------
def start_node():
    """
    Start the PADI Bureau Node with multi-network support.
    Initializes Weaver and Executor, displays network status,
    and runs the main event loop for signal processing and execution.
    """
    logger.info(f"--- 🏛️ STARTING PADI BUREAU: {Config.NODE_ID} ---")
    logger.info()

    # 1. Configuration Validation
    logger.info("=== Configuration Validation ===")
    if not Config.validate():
        logger.critical("❌ Configuration invalid. Aborting startup.")
        return
    logger.info("✅ Configuration validated.")
    logger.info()

    # 2. Display Network Configuration
    logger.info("=== Network Configuration ===")
    configured_networks = Config.get_configured_networks()
    for network_type, config in configured_networks.items():
        logger.info(f"  ✅ {config['name']} (Chain ID: {config['chain_id']})")
    logger.info(f"  Default Network: {Config.DEFAULT_NETWORK_TYPE}")
    logger.info(f"  Cross-Network Verification: {Config.DEFAULT_CROSS_NETWORK_VERIFICATION}")
    logger.info()

    # 3. Initialize Components
    logger.info("=== Component Initialization ===")
    try:
        weaver = Weaver()
        logger.info("✅ Weaver (Nervous System) initialized.")
        
        executor = Executor()
        logger.info("✅ Executor (Execution Layer) initialized.")
        
        logger.info("✅ All components initialized successfully.")
        logger.info()
    except Exception as e:
        logger.critical(f"❌ Component Initialization Failed: {e}")
        return

    # 4. Display Network Status
    logger.info("=== Network Status ===")
    weaver_status = weaver.get_network_status()
    executor_status = executor.get_network_status()
    
    networks = set(list(weaver_status.keys()) + list(executor_status.keys()))
    
    for network in sorted(networks):
        weaver_connected = weaver_status.get(network, {}).get("connected", False)
        executor_connected = executor_status.get(network, {}).get("connected", False)
        
        if weaver_connected and executor_connected:
            status = "✅ Fully Connected"
        elif weaver_connected:
            status = "⚠️ Weaver Only"
        elif executor_connected:
            status = "⚠️ Executor Only"
        else:
            status = "❌ Disconnected"
        
        network_name = weaver_status.get(network, {}).get("name", executor_status.get(network, {}).get("name", network))
        logger.info(f"  {network_name}: {status}")
    logger.info()

    # 5. Display Validation Rules
    logger.info("=== Validation Rules (1003 Rule) ===")
    logger.info(f"  Required Confidence: {Config.REQUIRED_CONFIDENCE}")
    logger.info(f"  Required Verification Sources: {Config.REQUIRED_VERIFICATION_SOURCES}")
    logger.info()

    # 6. Main Event Loop
    logger.info("=== Main Event Loop ===")
    logger.info(f"📡 Node-01 is now LIVE and observing networks: {', '.join(configured_networks.keys())}")
    logger.info(f"⏱️ Polling interval: {getattr(Config, 'POLLING_INTERVAL', 5)} seconds")
    logger.info()

    # Statistics tracking
    total_signals_processed = 0
    total_facts_promoted = 0
    total_transactions_executed = 0
    last_stats_time = time.time()
    stats_report_interval = 300  # Report stats every 5 minutes (300 seconds)

    while not shutdown_event.is_set():
        try:
            # A. Fetch and Validate Signals
            # Replace the empty list with a live feed from mempool/webhooks
            promoted_graphs = weaver.process_batch([])

            # B. Execute Facts
            if promoted_graphs:
                total_facts_promoted += len(promoted_graphs)
                logger.info(
                    f"⚖️ Detected {len(promoted_graphs)} validated signals. "
                    f"Dispatching to Executor..."
                )
                receipts = executor.execute_batch(promoted_graphs)
                
                successful_transactions = sum(1 for r in receipts if r is not None)
                total_transactions_executed += successful_transactions
                
                logger.info(
                    f"📝 Batch Processed. Successful: {successful_transactions}/{len(promoted_graphs)}. "
                    f"Receipts: {[r for r in receipts if r is not None]}"
                )

            # C. Periodic Statistics Reporting
            current_time = time.time()
            if current_time - last_stats_time >= stats_report_interval:
                log_statistics(
                    total_signals_processed,
                    total_facts_promoted,
                    total_transactions_executed,
                    weaver,
                    executor
                )
                last_stats_time = current_time

            # D. Throttle RPC Polling
            polling_interval = getattr(Config, 'POLLING_INTERVAL', 5)
            time.sleep(polling_interval)

        except KeyboardInterrupt:
            logger.info(f"🛑 Shutdown signal received. {Config.NODE_ID} going offline.")
            break
        except Exception as e:
            logger.error(f"💥 UNHANDLED ERROR in main loop: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Retry after brief sleep to handle transient network issues
            time.sleep(3)
        finally:
            # Optional: Could persist state or perform cleanup here
            pass

    # 7. Shutdown Reporting
    logger.info()
    logger.info("=== Shutdown Report ===")
    logger.info(f"Total Signals Processed: {total_signals_processed}")
    logger.info(f"Total Facts Promoted: {total_facts_promoted}")
    logger.info(f"Total Transactions Executed: {total_transactions_executed}")
    
    # Final execution statistics
    logger.info()
    logger.info("=== Final Execution Statistics ===")
    stats = executor.get_execution_stats()
    for network, stat in stats.items():
        logger.info(
            f"  {network}: "
            f"✅ {stat.get('successful', 0)} | "
            f"❌ {stat.get('failed', 0)} | "
            f"⏭️ {stat.get('skipped', 0)}"
        )
    
    logger.info()
    logger.info("🛑 Node shutdown complete.")


def log_statistics(
    total_signals_processed: int,
    total_facts_promoted: int,
    total_transactions_executed: int,
    weaver: Weaver,
    executor: Executor
):
    """
    Log operational statistics.
    
    Args:
        total_signals_processed: Total number of signals processed
        total_facts_promoted: Total number of facts promoted
        total_transactions_executed: Total number of successful transactions
        weaver: Weaver instance
        executor: Executor instance
    """
    logger.info()
    logger.info("=== Operational Statistics ===")
    logger.info(f"  Total Signals Processed: {total_signals_processed}")
    logger.info(f"  Total Facts Promoted: {total_facts_promoted}")
    logger.info(f"  Total Transactions Executed: {total_transactions_executed}")
    
    # Execution statistics per network
    stats = executor.get_execution_stats()
    if any(s.get('successful', 0) > 0 or s.get('failed', 0) > 0 or s.get('skipped', 0) > 0 for s in stats.values()):
        logger.info()
        logger.info("  Execution Statistics by Network:")
        for network, stat in stats.items():
            if stat.get('successful', 0) > 0 or stat.get('failed', 0) > 0 or stat.get('skipped', 0) > 0:
                logger.info(
                    f"    {network}: "
                    f"✅ {stat.get('successful', 0)} | "
                    f"❌ {stat.get('failed', 0)} | "
                    f"⏭️ {stat.get('skipped', 0)}"
                )
    
    # Network status
    weaver_status = weaver.get_network_status()
    disconnected_networks = [name for name, info in weaver_status.items() if not info.get("connected")]
    if disconnected_networks:
        logger.info()
        logger.warning(f"  ⚠️ Disconnected Networks: {', '.join(disconnected_networks)}")
    
    logger.info()
    logger.info("=== End of Statistics Report ===")
    logger.info()


def run_test_mode():
    """
    Run a test mode with demo signals to validate multi-network functionality.
    """
    logger.info("=== TEST MODE ===")
    logger.info("Running in test mode with demo signals...")
    logger.info()

    # Initialize components
    try:
        weaver = Weaver()
        executor = Executor()
    except Exception as e:
        logger.error(f"❌ Component initialization failed: {e}")
        return

    # Demo signals for multiple networks
    demo_signals = [
        # OP Mainnet Signal
        {
            "label": "Demo_OP_Mainnet_001",
            "confidence": 1.0,
            "sources": ["Pyth-Demo", "Chainlink-Demo", "Uniswap-Demo"],
            "target": "0x4752ba5DBc23f44D620376279d4b37A730947593",
            "action": "ARBITRAGE",
            "uid": "DEMO-OP-001",
            "network_type": "op-mainnet",
            "source_provider": "Alchemy-OP-Mainnet",
            "verification_confidence": [1.0, 1.0, 1.0],
            "verification_timestamp": ["2026-03-26T01:50:00Z", "2026-03-26T01:50:01Z", "2026-03-26T01:50:02Z"],
            "verification_match": [True, True, True],
            "primary_network": "op-mainnet",
            "fallback_network": "eth-mainnet",
            "cross_network_verification": True
        },
        # Ethereum Mainnet Signal
        {
            "label": "Demo_ETH_Mainnet_001",
            "confidence": 1.0,
            "sources": ["Pyth-Demo", "Chainlink-Demo", "Uniswap-Demo"],
            "target": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            "action": "SWAP",
            "uid": "DEMO-ETH-001",
            "network_type": "eth-mainnet",
            "source_provider": "Alchemy-ETH-Mainnet",
            "verification_confidence": [1.0, 1.0, 1.0],
            "verification_timestamp": ["2026-03-26T01:50:03Z", "2026-03-26T01:50:04Z", "2026-03-26T01:50:05Z"],
            "verification_match": [True, True, True],
            "primary_network": "eth-mainnet",
            "cross_network_verification": True
        }
    ]

    # Process demo signals
    logger.info("Processing demo signals...")
    promoted_graphs = weaver.process_batch(demo_signals)

    # Execute demo facts
    if promoted_graphs:
        # In read-only mode (no private key), transactions will be skipped
        receipts = executor.execute_batch(promoted_graphs)
        logger.info(f"Demo batch processed. Receipts: {receipts}")

    # Display final statistics
    stats = executor.get_execution_stats()
    logger.info()
    logger.info("=== Test Mode Statistics ===")
    for network, stat in stats.items():
        if stat.get('successful', 0) > 0 or stat.get('failed', 0) > 0 or stat.get('skipped', 0) > 0:
            logger.info(
                f"  {network}: "
                f"✅ {stat.get('successful', 0)} | "
                f"❌ {stat.get('failed', 0)} | "
                f"⏭️ {stat.get('skipped', 0)}"
            )

    logger.info()
    logger.info("=== Test Mode Complete ===")


# ---------------------------
# Standalone Execution
# ---------------------------
if __name__ == "__main__":
    import sys
    
    # Check for test mode flag
    if "--test" in sys.argv:
        run_test_mode()
    else:
        start_node()
