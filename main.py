import time
import signal
import logging
from config import Config
from weaver import Weaver
from executor import Executor

# =====================================================
# 🏛️ PADI BUREAU — NAIROBI NODE-01
# main.py — Production Entry Point / Process Manager
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
def shutdown_handler(sig, frame):
    logger.info("🛑 SIGINT received. Shutting down Nairobi Node gracefully...")
    exit(0)

signal.signal(signal.SIGINT, shutdown_handler)

# ---------------------------
# Node Bootstrap
# ---------------------------
def start_node():
    logger.info(f"--- 🏛️ STARTING PADI BUREAU: {Config.NODE_ID} ---")

    # 1. Config Validation
    if not Config.validate():
        logger.critical("❌ Configuration invalid. Aborting startup.")
        return

    # 2. Initialize Components
    try:
        weaver = Weaver()
        executor = Executor()
        logger.info("✅ Nervous System and Execution Layer Initialized.")
    except Exception as e:
        logger.critical(f"❌ Component Initialization Failed: {e}")
        return

    # 3. Main Event Loop
    logger.info("📡 Node-01 is now LIVE and observing Base L2.")
    while True:
        try:
            # A. Fetch and Validate Signals
            # Replace the empty list with a live feed from mempool/webhooks
            promoted_graphs = weaver.process_batch([])

            # B. Execute Facts
            if promoted_graphs:
                logger.info(f"⚖️ Detected {len(promoted_graphs)} validated signals. Dispatching to Executor...")
                receipts = executor.execute_batch(promoted_graphs)
                logger.info(f"📝 Batch Processed. Receipts: {receipts}")

            # C. Throttle RPC Polling
            time.sleep(5)  # configurable via Config in future iterations

        except KeyboardInterrupt:
            logger.info(f"🛑 Shutdown signal received. {Config.NODE_ID} going offline.")
            break
        except Exception as e:
            logger.error(f"💥 UNHANDLED ERROR in main loop: {e}")
            # Retry after brief sleep to handle transient network issues
            time.sleep(3)
        finally:
            # Optional: Could persist state or perform cleanup here
            pass

# ---------------------------
# Standalone Execution
# ---------------------------
if __name__ == "__main__":
    start_node()
