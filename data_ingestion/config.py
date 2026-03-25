import os
from dotenv import load_dotenv
from typing import Optional, Dict
from pathlib import Path

# =====================================================
# 🏛️ PADI CONFIGURATION v4.0 — NAIROBI NODE-01
# Multi-Network Support: OP Mainnet, OP Sepolia, ETH Mainnet, ETH Sepolia
# =====================================================

# Load environment variables from .env file
load_dotenv()

# =====================================================
# 🏛️ NODE IDENTIFICATION
# =====================================================

NODE_ID = os.getenv("PADI_NODE_ID", "NAIROBI-01")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# =====================================================
# 🏛️ WALLET CONFIGURATION
# =====================================================

PADI_WALLET_ADDRESS = os.getenv("PADI_WALLET_ADDRESS")
PADI_PRIVATE_KEY = os.getenv("PADI_PRIVATE_KEY")

# =====================================================
# 🏛️ MULTI-NETWORK RPC CONFIGURATION
# =====================================================

# ---------------------------
# OP Mainnet Configuration
# ---------------------------
# RPC Endpoint for Optimism Mainnet
# Example: https://opt-mainnet.g.alchemy.com/v2/YOUR_API_KEY
# Example: https://mainnet.optimism.io
OP_MAINNET_RPC_URL = os.getenv("OP_MAINNET_RPC_URL")

# ---------------------------
# OP Sepolia Configuration
# ---------------------------
# RPC Endpoint for Optimism Sepolia Testnet
# Example: https://opt-sepolia.g.alchemy.com/v2/YOUR_API_KEY
# Example: https://sepolia.optimism.io
OP_SEPOLIA_RPC_URL = os.getenv("OP_SEPOLIA_RPC_URL")

# ---------------------------
# Ethereum Mainnet Configuration
# ---------------------------
# RPC Endpoint for Ethereum Mainnet
# Example: https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY
# Example: https://mainnet.infura.io/v3/YOUR_PROJECT_ID
ETH_MAINNET_RPC_URL = os.getenv("ETH_MAINNET_RPC_URL")

# ---------------------------
# Ethereum Sepolia Configuration
# ---------------------------
# RPC Endpoint for Ethereum Sepolia Testnet
# Example: https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY
# Example: https://sepolia.infura.io/v3/YOUR_PROJECT_ID
ETH_SEPOLIA_RPC_URL = os.getenv("ETH_SEPOLIA_RPC_URL")

# =====================================================
# 🏛️ LEGACY BASE L2 CONFIGURATION (BACKWARD COMPATIBILITY)
# =====================================================

# ---------------------------
# Base L2 Configuration
# ---------------------------
# RPC Endpoint for Base L2
# Example: https://base-mainnet.g.alchemy.com/v2/YOUR_API_KEY
# Example: https://mainnet.base.org
# Note: This is maintained for backward compatibility only
BASE_L2_RPC_URL = os.getenv("BASE_L2_RPC_URL")

# ---------------------------
# Chain ID Configuration
# ---------------------------
# Default chain ID for legacy Base L2 operations
# Note: Multi-network executor uses NETWORK_CONFIG instead
CHAIN_ID = int(os.getenv("CHAIN_ID", "8453"))  # Default: Base L2

# =====================================================
# 🏛️ SCHEMA CONFIGURATION
# =====================================================

# Paths to RDF schema files
ONTology_FILE = os.getenv("ONTology_FILE", "schema/ontology.ttl")
SHAPES_FILE = os.getenv("SHAPES_FILE", "schema/shapes.ttl")
RULES_FILE = os.getenv("RULES_FILE", "schema/rules.ttl")

# =====================================================
# 🏛️ AUDIT CONFIGURATION
# =====================================================

# Audit log directory
AUDIT_LOG_DIR = os.getenv("AUDIT_LOG_DIR", "audit_logs")

# Maximum audit log size (in MB) before rotation
AUDIT_LOG_MAX_SIZE_MB = int(os.getenv("AUDIT_LOG_MAX_SIZE_MB", "100"))

# Maximum number of backup audit logs to retain
AUDIT_LOG_MAX_BACKUPS = int(os.getenv("AUDIT_LOG_MAX_BACKUPS", "10"))

# =====================================================
# 🏛️ EXECUTION CONFIGURATION
# =====================================================

# Default gas price override (in wei)
# Set to None to use network gas price
DEFAULT_GAS_PRICE = os.getenv("DEFAULT_GAS_PRICE")

# Gas limit for transactions
GAS_LIMIT = int(os.getenv("GAS_LIMIT", "250000"))

# Transaction timeout (in seconds)
TX_TIMEOUT = int(os.getenv("TX_TIMEOUT", "300"))

# =====================================================
# 🏛️ MULTI-NETWORK CONFIGURATION
# =====================================================

# Default network type for operations when not specified
# Options: "op-mainnet", "op-sepolia", "eth-mainnet", "eth-sepolia", "base-l2" (legacy)
DEFAULT_NETWORK_TYPE = os.getenv("DEFAULT_NETWORK_TYPE", "op-mainnet")

# Enable cross-network verification by default
DEFAULT_CROSS_NETWORK_VERIFICATION = os.getenv("DEFAULT_CROSS_NETWORK_VERIFICATION", "true").lower() == "true"

# Fallback network order (list of networks to try in order)
FALLBACK_NETWORK_ORDER = os.getenv("FALLBACK_NETWORK_ORDER", "op-mainnet,eth-mainnet,op-sepolia,eth-sepolia").split(",")

# =====================================================
# 🏛️ VALIDATION RULES
# =====================================================

# Required confidence score for deterministic execution (1003 Rule)
REQUIRED_CONFIDENCE = float(os.getenv("REQUIRED_CONFIDENCE", "1.0"))

# Required number of verification sources (1003 Rule)
REQUIRED_VERIFICATION_SOURCES = int(os.getenv("REQUIRED_VERIFICATION_SOURCES", "3"))

# =====================================================
# 🏛️ VALIDATION METHODS
# =====================================================

def validate() -> bool:
    """
    Validate configuration settings.
    Returns True if configuration is valid, False otherwise.
    """
    # Check wallet configuration
    if not PADI_WALLET_ADDRESS:
        print("⚠️ Warning: PADI_WALLET_ADDRESS not configured.")
    
    if not PADI_PRIVATE_KEY:
        print("⚠️ Warning: PADI_PRIVATE_KEY not configured. Read-only mode enabled.")
    
    # Check RPC configuration (at least one network must be configured)
    rpc_urls = [
        ("OP Mainnet", OP_MAINNET_RPC_URL),
        ("OP Sepolia", OP_SEPOLIA_RPC_URL),
        ("Ethereum Mainnet", ETH_MAINNET_RPC_URL),
        ("Ethereum Sepolia", ETH_SEPOLIA_RPC_URL),
        ("Base L2", BASE_L2_RPC_URL)
    ]
    
    configured_networks = [name for name, url in rpc_urls if url]
    
    if not configured_networks:
        print("❌ Error: No RPC URLs configured. At least one network must be configured.")
        return False
    
    print(f"✅ Configured networks: {', '.join(configured_networks)}")
    
    # Validate network types
    if DEFAULT_NETWORK_TYPE not in ["op-mainnet", "op-sepolia", "eth-mainnet", "eth-sepolia", "base-l2"]:
        print(f"⚠️ Warning: Invalid DEFAULT_NETWORK_TYPE: {DEFAULT_NETWORK_TYPE}")
        return False
    
    # Validate confidence and verification sources
    if REQUIRED_CONFIDENCE < 0.0 or REQUIRED_CONFIDENCE > 1.0:
        print(f"❌ Error: REQUIRED_CONFIDENCE must be between 0.0 and 1.0, got {REQUIRED_CONFIDENCE}")
        return False
    
    if REQUIRED_VERIFICATION_SOURCES < 1:
        print(f"❌ Error: REQUIRED_VERIFICATION_SOURCES must be at least 1, got {REQUIRED_VERIFICATION_SOURCES}")
        return False
    
    # Validate audit log directory
    audit_dir_path = Path(AUDIT_LOG_DIR)
    try:
        audit_dir_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"❌ Error: Failed to create audit log directory: {e}")
        return False
    
    return True


def get_network_config(network_type: str) -> Dict[str, any]:
    """
    Get network configuration for a specific network type.
    
    Args:
        network_type: Network type ("op-mainnet", "op-sepolia", "eth-mainnet", "eth-sepolia", "base-l2")
    
    Returns:
        Dictionary with network configuration (chain_id, rpc_url, name)
    
    Raises:
        ValueError: If network_type is invalid or not configured
    """
    configs = {
        "op-mainnet": {
            "chain_id": 10,
            "rpc_url": OP_MAINNET_RPC_URL,
            "name": "OP Mainnet",
            "network_type": "layer2"
        },
        "op-sepolia": {
            "chain_id": 11155420,
            "rpc_url": OP_SEPOLIA_RPC_URL,
            "name": "OP Sepolia",
            "network_type": "layer2-testnet"
        },
        "eth-mainnet": {
            "chain_id": 1,
            "rpc_url": ETH_MAINNET_RPC_URL,
            "name": "Ethereum Mainnet",
            "network_type": "layer1"
        },
        "eth-sepolia": {
            "chain_id": 11155111,
            "rpc_url": ETH_SEPOLIA_RPC_URL,
            "name": "Ethereum Sepolia",
            "network_type": "layer1-testnet"
        },
        "base-l2": {
            "chain_id": CHAIN_ID,
            "rpc_url": BASE_L2_RPC_URL,
            "name": "Base L2",
            "network_type": "layer2-legacy"
        }
    }
    
    if network_type not in configs:
        raise ValueError(f"Invalid network_type: {network_type}. Must be one of {list(configs.keys())}")
    
    config = configs[network_type]
    
    if not config["rpc_url"]:
        raise ValueError(f"RPC URL not configured for {network_type}. Please set the environment variable.")
    
    return config


def get_configured_networks() -> Dict[str, Dict[str, any]]:
    """
    Get all configured networks.
    
    Returns:
        Dictionary mapping network types to their configurations
        Only includes networks with configured RPC URLs
    """
    all_configs = {
        "op-mainnet": {
            "chain_id": 10,
            "rpc_url": OP_MAINNET_RPC_URL,
            "name": "OP Mainnet",
            "network_type": "layer2"
        },
        "op-sepolia": {
            "chain_id": 11155420,
            "rpc_url": OP_SEPOLIA_RPC_URL,
            "name": "OP Sepolia",
            "network_type": "layer2-testnet"
        },
        "eth-mainnet": {
            "chain_id": 1,
            "rpc_url": ETH_MAINNET_RPC_URL,
            "name": "Ethereum Mainnet",
            "network_type": "layer1"
        },
        "eth-sepolia": {
            "chain_id": 11155111,
            "rpc_url": ETH_SEPOLIA_RPC_URL,
            "name": "Ethereum Sepolia",
            "network_type": "layer1-testnet"
        },
        "base-l2": {
            "chain_id": CHAIN_ID,
            "rpc_url": BASE_L2_RPC_URL,
            "name": "Base L2",
            "network_type": "layer2-legacy"
        }
    }
    
    # Filter to only include configured networks
    return {network: config for network, config in all_configs.items() if config["rpc_url"]}


def validate_network_config(network_type: str) -> tuple[bool, str]:
    """
    Validate network configuration for a specific network.
    
    Args:
        network_type: Network type to validate
    
    Returns:
        Tuple of (is_valid, error_message)
        is_valid: True if configuration is valid, False otherwise
        error_message: Error message if invalid, empty string if valid
    """
    try:
        config = get_network_config(network_type)
        return True, ""
    except ValueError as e:
        return False, str(e)


# =====================================================
# 🏛️ DISPLAY CONFIGURATION (for debugging)
# =====================================================

def display_config():
    """Display current configuration settings."""
    print("=" * 60)
    print("🏛️ PADI SOVEREIGN BUREAU — NODE CONFIGURATION")
    print("=" * 60)
    print()
    print("Node Identification:")
    print(f"  Node ID: {NODE_ID}")
    print(f"  Log Level: {LOG_LEVEL}")
    print()
    print("Wallet Configuration:")
    print(f"  Wallet Address: {PADI_WALLET_ADDRESS or 'Not configured'}")
    print(f"  Private Key: {'Configured' if PADI_PRIVATE_KEY else 'Not configured (read-only)'}")
    print()
    print("Network Configuration:")
    configured = get_configured_networks()
    if configured:
        for network, config in configured.items():
            print(f"  ✅ {config['name']} (Chain ID: {config['chain_id']})")
        print(f"  Default Network: {DEFAULT_NETWORK_TYPE}")
    else:
        print(f"  ❌ No networks configured")
    print()
    print("Validation Rules (1003 Rule):")
    print(f"  Required Confidence: {REQUIRED_CONFIDENCE}")
    print(f"  Required Verification Sources: {REQUIRED_VERIFICATION_SOURCES}")
    print()
    print("Execution Configuration:")
    print(f"  Gas Limit: {GAS_LIMIT}")
    print(f"  Transaction Timeout: {TX_TIMEOUT} seconds")
    print(f"  Cross-Network Verification: {DEFAULT_CROSS_NETWORK_VERIFICATION}")
    print()
    print("Schema Configuration:")
    print(f"  Ontology File: {ONTology_FILE}")
    print(f"  Shapes File: {SHAPES_FILE}")
    print(f"  Rules File: {RULES_FILE}")
    print()
    print("=" * 60)


# =====================================================
# 🏛️ STANDALONE ENTRY
# =====================================================

if __name__ == "__main__":
    print("🏛️ PADI CONFIGURATION VALIDATION")
    print()
    
    if validate():
        print("✅ Configuration is valid.")
        print()
        display_config()
    else:
        print("❌ Configuration validation failed.")
        print("Please check your environment variables and try again.")
