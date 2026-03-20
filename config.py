import os
from pathlib import Path
from dotenv import load_dotenv

# =====================================================
# 🏛️ PADI BUREAU — NAIROBI NODE-01 CONFIGURATION
# Phase Two: Nervous System (Logic & Environment)
# =====================================================

# Load .env variables from the root directory
load_dotenv()

class Config:
    """
    Centralized configuration for the PADI Bureau.
    Ensures all components (Weaver, Auditor, Executor) use the 
    same paths, endpoints, and security constraints.
    """

    # ---------------------------
    # Infrastructure (Base L2)
    # ---------------------------
    BASE_L2_RPC_URL = os.getenv("BASE_L2_RPC_URL")
    NODE_ID = os.getenv("NODE_ID", "NAIROBI-NODE-01")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Robust Boolean Parsing for Debug Mode
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Optional Wallet / Execution Layer (Phase 3 Preparation)
    PADI_WALLET_ADDRESS = os.getenv("PADI_WALLET_ADDRESS")
    PADI_PRIVATE_KEY = os.getenv("PADI_PRIVATE_KEY")

    # ---------------------------
    # Semantic Engine Paths
    # ---------------------------
    # Uses pathlib for cross-platform (Linux/Nairobi Node) compatibility
    BASE_DIR = Path(__file__).parent
    
    # Safe path resolution for Ontology and SHACL shapes
    _ont_file = os.getenv("ONTOLOGY_PATH", "schema/ontology.ttl")
    _shp_file = os.getenv("SHAPES_PATH", "schema/shapes.ttl")
    
    ONTOLOGY_PATH = str(BASE_DIR / _ont_file)
    SHAPES_PATH = str(BASE_DIR / _shp_file)

    # ---------------------------
    # Execution & Batch Parameters
    # ---------------------------
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", 50))

    # ---------------------------
    # Validation Method
    # ---------------------------
    @classmethod
    def validate(cls):
        """
        Checks if the minimum required config is present.
        Prevents the Bureau from starting with 'Mock' or missing data.
        """
        is_valid = True

        # 1. RPC Check
        if not cls.BASE_L2_RPC_URL or "YOUR_API_KEY" in cls.BASE_L2_RPC_URL:
            print("❌ CRITICAL: BASE_L2_RPC_URL is missing or contains placeholder.")
            is_valid = False

        # 2. Private Key Safety Check
        if cls.PADI_PRIVATE_KEY and cls.PADI_PRIVATE_KEY.startswith("Your"):
            print("⚠️ WARNING: PADI_PRIVATE_KEY placeholder detected. Safety Lock Engaged.")
            is_valid = False

        # 3. Path Verification
        if not Path(cls.ONTOLOGY_PATH).exists():
            print(f"❌ CRITICAL: Ontology not found at {cls.ONTOLOGY_PATH}")
            is_valid = False
            
        if not Path(cls.SHAPES_PATH).exists():
            print(f"❌ CRITICAL: SHACL Shapes not found at {cls.SHAPES_PATH}")
            is_valid = False

        # 4. Debug Feedback
        if cls.DEBUG and is_valid:
            print(f"🔧 [DEBUG] Node: {cls.NODE_ID} | RPC: {cls.BASE_L2_RPC_URL[:25]}...")
            print(f"🔧 [DEBUG] Ontology: {cls.ONTOLOGY_PATH}")

        return is_valid

# ---------------------------
# Standalone Diagnostics
# ---------------------------
if __name__ == "__main__":
    print(f"--- 🏛️ PADI CONFIG DIAGNOSTICS: {Config.NODE_ID} ---")
    if Config.validate():
        print("✅ Configuration is PRODUCTION READY.")
    else:
        print("❌ Configuration FAILED. Correct your .env file.")
