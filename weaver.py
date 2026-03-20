import time
from web3 import Web3
from datetime import datetime
from config import Config
from bureau_core import audit_signal

# =====================================================
# 🏛️ PADI WEAVER — NAIROBI NODE-01
# Phase Two: Nervous System with Batch Signal Ingestion
# =====================================================

class Weaver:
    """
    The Weaver synchronizes external signals with live blockchain context
    and triggers the SHACL-enforced Audit in batch or individually.
    """

    def __init__(self):
        # 1. Validate configuration
        if not Config.validate():
            raise ConnectionError("❌ Weaver aborted: Invalid Configuration.")
        
        # 2. Connect to Base L2 network
        self.w3 = Web3(Web3.HTTPProvider(Config.BASE_L2_RPC_URL))
        self.node_id = Config.NODE_ID
        
        if self.w3.is_connected():
            print(f"🚀 {self.node_id}: Connected to Base L2.")
        else:
            raise ConnectionError(f"❌ {self.node_id}: Failed to connect to Base RPC.")

    # ---------------------------
    # Live network context
    # ---------------------------
    def get_live_context(self):
        """Fetch latest block and gas price from Base L2."""
        try:
            latest_block = self.w3.eth.get_block('latest')
            gas_price = self.w3.from_wei(self.w3.eth.gas_price, 'gwei')
            return {
                "block_number": latest_block['number'],
                "gas_price": float(gas_price),
                "timestamp": datetime.fromtimestamp(latest_block['timestamp']).isoformat()
            }
        except Exception as e:
            print(f"📡 RPC Sync Error: {e}")
            return None

    # ---------------------------
    # Process a single signal
    # ---------------------------
    def process_signal(self, raw_data):
        ctx = self.get_live_context()
        if not ctx:
            print("🛡️ Safety Lock: Signal rejected due to Infrastructure Desync.")
            return None

        print(f"\n--- 🧵 Weaving Signal: {raw_data.get('label', 'Unknown')} ---")
        graph, conforms, status, report = audit_signal(
            name=raw_data.get("label", f"SIG-{int(time.time())}"),
            confidence=raw_data.get("confidence", 0.0),
            sources=raw_data.get("sources", []),
            target_address=raw_data.get("target", "0x000"),
            action_type=raw_data.get("action", "OBSERVE"),
            signal_id=raw_data.get("uid", f"SIG-{int(time.time())}"),
            block_number=ctx["block_number"],
            gas_price_gwei=ctx["gas_price"],
            observed_at=ctx["timestamp"],
            is_validated=False
        )

        # 3. Reporting
        if conforms:
            print(f"✅ DETERMINISTIC: Signal promoted to ExecutableFact.")
            print(f"📍 Target: {raw_data.get('target')} | Block: {ctx['block_number']}")
        else:
            print(f"❌ PROBABILISTIC: Signal Blocked by Sentinel.")
            if Config.DEBUG:
                print(f"Reasoning:\n{report}")

        return graph if conforms else None

    # ---------------------------
    # Batch signal processing
    # ---------------------------
    def process_batch(self, signals):
        """
        Processes multiple signals in a deterministic batch.
        Each signal is validated and promoted individually.
        """
        print(f"\n--- 🔄 Weaver: Processing batch of {len(signals)} signals ---")
        results = []
        for sig in signals:
            graph = self.process_signal(sig)
            if graph:
                results.append(graph)
        print(f"✅ Batch complete: {len(results)}/{len(signals)} signals promoted.")
        return results

# ---------------------------
# Example / Standalone Test
# ---------------------------
if __name__ == "__main__":
    weaver = Weaver()

    # Example batch of simulated signals (replace with real mempool/API calls)
    mock_batch = [
        {
            "label": "Alpha_Arb_001",
            "confidence": 1.0,
            "sources": ["Pyth", "Chainlink", "Uniswap_Events"],
            "target": "0x4752ba5DBc23f44D620376279d4b37A730947593",
            "action": "ARBITRAGE",
            "uid": "BASE-TX-001"
        },
        {
            "label": "Beta_Arb_002",
            "confidence": 0.9,  # Should fail 1003 Rule
            "sources": ["Pyth"],
            "target": "0x9999ba5DBc23f44D620376279d4b37A730947999",
            "action": "SWAP",
            "uid": "BASE-TX-002"
        }
    ]

    weaver.process_batch(mock_batch)
