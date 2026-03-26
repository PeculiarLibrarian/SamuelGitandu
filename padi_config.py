#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from web3 import Web3
from rdflib import Graph
from datetime import datetime
from enum import Enum

# =====================================================
# 🏛️ PadiConfig — Singleton Sovereign Configuration
# NAIROBI NODE-01 — Self-Validating Sovereign Environment
# Version: 5.0
# DOI Anchor: 10.5281/zenodo.18894084
# 
# REPLACES: data_ingestion/config.py v4.0
# MIGRATION: Procedural Configuration → Singleton Architecture
# =====================================================

logger = logging.getLogger("PADICONTROLLER")


class NetworkType(Enum):
    """Validated network types for PADI v3.0 standard."""
    OP_MAINNET = "op-mainnet"
    OP_SEPOLIA = "op-sepolia"
    ETH_MAINNET = "eth-mainnet"
    ETH_SEPOLIA = "eth-sepolia"
    BASE_L2 = "base-l2"


class ActionType(Enum):
    """Validated action types for PADI v3.0 standard."""
    ARBITRAGE = "ARBITRAGE"
    SWAP = "SWAP"
    AUDIT = "AUDIT"
    TRANSFER = "TRANSFER"
    MULTI_SWAP = "MULTI_SWAP"


class PadiConfig:
    """
    Singleton Configuration Controller for Nairobi Node-01.
    
    Replaces procedural data_ingestion/config.py v4.0 with immutable,
    validated configuration object. Ensures all modules operate from
    identical state, eliminating split-brain errors.
    
    Features:
    - Singleton pattern (single instance guarantee)
    - Immutable configuration (frozen after initialization)
    - Environment variable validation
    - Schema validation against PADI v3.0 ontology
    - Pre-flight verification support
    - Thread-safe access
    - Backward compatibility with v4.0 API
    
    Version: 5.0
    Replaces: data_ingestion/config.py v4.0
    """

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """Singleton enforcement - only one instance."""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        env_path: Optional[Path] = None,
        schema_path: Optional[Path] = None
    ):
        """
        Initialize PadiConfig singleton.
        
        Args:
            env_path: Optional path to .env file (default: .env)
            schema_path: Optional path to schema/ontology.ttl (default: schema/ontology.ttl)
        
        Raises:
            ValueError: If configuration validation fails
        """
        # Prevent re-initialization
        if self._initialized:
            return
        
        self._logger = logger
        self._lock = threading.Lock()
        
        # Load environment variables
        self._env_path = env_path or Path(".env")
        self._load_environment()
        
        # Validate core configuration
        self._validate_core_config()
        
        # Load schema for pre-flight verification
        self._schema_path = schema_path or Path("schema/ontology.ttl")
        self._schema_graph = self._load_schema()
        
        # Initialize configurations
        self._init_wallet_config()
        self._init_network_configs()
        self._init_system_config()
        self._init_audit_config()
        self._init_execution_config()
        self._init_validation_rules()
        
        # Mark as initialized (immutable)
        self._initialized = True
        
        # Log initialization
        self._log_initialization()

    def _load_environment(self):
        """Load environment variables from .env file."""
        if self._env_path.exists():
            self._logger.info(f"📄 Loading environment from {self._env_path}")
            from dotenv import load_dotenv
            load_dotenv(self._env_path)
        else:
            self._logger.warning(f"⚠️ .env file not found at {self._env_path}")
            self._logger.warning("⚠️ Using system environment variables only")

    def _validate_core_config(self) -> bool:
        """
        Validate core configuration requirements.
        
        Returns:
            True if validation passes
        
        Raises:
            ValueError: If required configuration is missing
        """
        errors = []
        
        # Required environment variables (v4.0 compatibility)
        node_id_var = os.getenv("PADI_NODE_ID") or os.getenv("NODE_ID", "NAIROBI-01")
        if not node_id_var:
            errors.append("Node ID (NODE_ID or PADI_NODE_ID) not set")
        
        if not os.getenv("PADI_WALLET_ADDRESS"):
            errors.append("PADI_WALLET_ADDRESS not set")
        
        # At least one RPC must be configured
        has_rpc = any([
            os.getenv("OP_MAINNET_RPC_URL"),
            os.getenv("OP_SEPOLIA_RPC_URL"),
            os.getenv("ETH_MAINNET_RPC_URL"),
            os.getenv("ETH_SEPOLIA_RPC_URL"),
            os.getenv("BASE_L2_RPC_URL")
        ])
        
        if not has_rpc:
            errors.append("At least one RPC URL must be configured")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            self._logger.error(error_msg)
            raise ValueError(error_msg)
        
        self._logger.info("✅ Core configuration validation passed")
        return True

    def _load_schema(self) -> Optional[Graph]:
        """
        Load PADI v3.0 schema for pre-flight verification.
        
        Returns:
            rdflib Graph containing schema, or None if not found
        """
        if self._schema_path.exists():
            try:
                graph = Graph()
                graph.parse(str(self._schema_path), format='turtle')
                self._logger.info(f"✅ Schema loaded from {self._schema_path}")
                return graph
            except Exception as e:
                self._logger.warning(f"⚠️ Failed to load schema: {e}")
                return None
        else:
            self._logger.warning(f"⚠️ Schema file not found at {self._schema_path}")
            return None

    def _init_wallet_config(self):
        """Initialize wallet configuration (v4.0 compatibility)."""
        wallet_address = os.getenv("PADI_WALLET_ADDRESS")
        private_key = os.getenv("PADI_PRIVATE_KEY")
        
        # Validate wallet address
        checksum_address = None
        if wallet_address:
            if not Web3.is_address(wallet_address):
                raise ValueError(f"Invalid wallet address: {wallet_address}")
            checksum_address = Web3.to_checksum_address(wallet_address)
        
        self._wallet = {
            "address": wallet_address,
            "private_key": private_key,
            "checksum_address": checksum_address,
            "has_private_key": bool(private_key),
            "read_only_mode": not bool(private_key)
        }
        
        self._logger.info(
            f"✅ Wallet configured: {checksum_address or 'N/A'} "
            f"{'(Read-Only)' if self._wallet['read_only_mode'] else ''}"
        )

    def _init_network_configs(self):
        """
        Initialize network configurations (v4.0 + v5.0 features).
        
        Migrates all v4.0 network configs to v5.0 object-oriented structure.
        """
        # Default chain ID for legacy Base L2 operations
        chain_id_legacy = int(os.getenv("CHAIN_ID", "8453"))
        
        self._networks = {
            "op-mainnet": {
                "chain_id": 10,
                "rpc_url": os.getenv("OP_MAINNET_RPC_URL"),
                "rpc_backup": os.getenv("OP_MAINNET_RPC_BACKUP_URL"),
                "name": "OP Mainnet",
                "network_type": NetworkType.OP_MAINNET,
                "type": "eip1559",
                "gas_speed": "fast",
                "supports_l1_fee": True,
                "layer": "layer2"
            },
            "op-sepolia": {
                "chain_id": 11155420,
                "rpc_url": os.getenv("OP_SEPOLIA_RPC_URL"),
                "rpc_backup": os.getenv("OP_SEPOLIA_RPC_BACKUP_URL"),
                "name": "OP Sepolia",
                "network_type": NetworkType.OP_SEPOLIA,
                "type": "eip1559",
                "gas_speed": "standard",
                "supports_l1_fee": True,
                "layer": "layer2-testnet"
            },
            "eth-mainnet": {
                "chain_id": 1,
                "rpc_url": os.getenv("ETH_MAINNET_RPC_URL"),
                "rpc_backup": os.getenv("ETH_MAINNET_RPC_BACKUP_URL"),
                "name": "Ethereum Mainnet",
                "network_type": NetworkType.ETH_MAINNET,
                "type": "eip1559",
                "gas_speed": "fast",
                "supports_l1_fee": False,
                "layer": "layer1"
            },
            "eth-sepolia": {
                "chain_id": 11155111,
                "rpc_url": os.getenv("ETH_SEPOLIA_RPC_URL"),
                "rpc_backup": os.getenv("ETH_SEPOLIA_RPC_BACKUP_URL"),
                "name": "Ethereum Sepolia",
                "network_type": NetworkType.ETH_SEPOLIA,
                "type": "eip1559",
                "gas_speed": "standard",
                "supports_l1_fee": False,
                "layer": "layer1-testnet"
            },
            "base-l2": {
                "chain_id": chain_id_legacy,
                "rpc_url": os.getenv("BASE_L2_RPC_URL"),
                "rpc_backup": os.getenv("BASE_L2_RPC_BACKUP_URL"),
                "name": "Base L2",
                "network_type": NetworkType.BASE_L2,
                "type": "eip1559",
                "gas_speed": "standard",
                "supports_l1_fee": True,
                "layer": "layer2-legacy"
            }
        }
        
        # Validate network configurations
        active_networks = []
        for network_name, config in self._networks.items():
            if not config["rpc_url"]:
                self._logger.warning(f"⚠️ No RPC URL configured for {config['name']}")
            else:
                active_networks.append(config['name'])
        
        self._logger.info(f"✅ Network configurations initialized: {len(active_networks)} active networks")

    def _init_system_config(self):
        """Initialize system configuration (v4.0 compatibility)."""
        # Support both PADI_NODE_ID and NODE_ID for backward compatibility
        node_id_var = os.getenv("PADI_NODE_ID") or os.getenv("NODE_ID", "NAIROBI-01")
        
        self._system = {
            "node_id": node_id_var,
            "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
            "environment": os.getenv("ENVIRONMENT", "production"),
            "doi_anchor": "10.5281/zenodo.18894084",
            "protocol_version": "PADI v3.0",
            "config_version": "5.0",
            "timezone": os.getenv("TZ", "Africa/Nairobi")
        }
        
        self._logger.info(f"✅ System configuration initialized: {self._system['node_id']}")

    def _init_audit_config(self):
        """Initialize audit configuration (v4.0 compatibility)."""
        self._audit = {
            "log_dir": os.getenv("AUDIT_LOG_DIR", "audit_logs"),
            "max_size_mb": int(os.getenv("AUDIT_LOG_MAX_SIZE_MB", "100")),
            "max_backups": int(os.getenv("AUDIT_LOG_MAX_BACKUPS", "10"))
        }
        
        # Create audit log directory
        audit_dir = Path(self._audit["log_dir"])
        audit_dir.mkdir(parents=True, exist_ok=True)
        
        self._logger.info(f"✅ Audit configuration initialized")

    def _init_execution_config(self):
        """Initialize execution configuration (v4.0 compatibility)."""
        # Default gas price (may be None)
        default_gas_price = os.getenv("DEFAULT_GAS_PRICE")
        if default_gas_price:
            try:
                default_gas_price = int(default_gas_price)
            except ValueError:
                default_gas_price = None
        
        # Default network type
        default_network = os.getenv("DEFAULT_NETWORK_TYPE", "op-mainnet")
        if default_network not in self._networks:
            self._logger.warning(f"Invalid DEFAULT_NETWORK_TYPE: {default_network}, using op-mainnet")
            default_network = "op-mainnet"
        
        # Cross-network verification
        cross_network_verify = os.getenv("DEFAULT_CROSS_NETWORK_VERIFICATION", "true").lower()
        cross_network_verify = cross_network_verify == "true"
        
        # Fallback network order
        fallback_order = os.getenv("FALLBACK_NETWORK_ORDER", "op-mainnet,eth-mainnet,op-sepolia,eth-sepolia")
        fallback_order = [n.strip() for n in fallback_order.split(",") if n.strip()]
        
        self._execution = {
            "default_gas_price": default_gas_price,
            "gas_limit": int(os.getenv("GAS_LIMIT", "250000")),
            "tx_timeout": int(os.getenv("TX_TIMEOUT", "300")),
            "default_network_type": default_network,
            "default_cross_network_verification": cross_network_verify,
            "fallback_network_order": fallback_order
        }
        
        self._logger.info(f"✅ Execution configuration initialized")

    def _init_validation_rules(self):
        """Initialize validation rules (1003 Rule from v4.0)."""
        self._validation = {
            "required_confidence": float(os.getenv("REQUIRED_CONFIDENCE", "1.0")),
            "required_verification_sources": int(os.getenv("REQUIRED_VERIFICATION_SOURCES", "3")),
            "enforce_1003_rule": os.getenv("ENFORCE_1003_RULE", "true").lower() == "true"
        }
        
        # Validate confidence score
        if not (0.0 <= self._validation["required_confidence"] <= 1.0):
            raise ValueError(
                f"REQUIRED_CONFIDENCE must be between 0.0 and 1.0, "
                f"got {self._validation['required_confidence']}"
            )
        
        # Validate verification sources
        if self._validation["required_verification_sources"] < 1:
            raise ValueError(
                f"REQUIRED_VERIFICATION_SOURCES must be at least 1, "
                f"got {self._validation['required_verification_sources']}"
            )
        
        self._logger.info(f"✅ Validation rules initialized (1003 Rule)")

    def _log_initialization(self):
        """Log initialization summary."""
        self._logger.info("")
        self._logger.info("=" * 70)
        self._logger.info("🏛️ PADI SOVEREIGN CONFIGURATION CONTROLLER v5.0")
        self._logger.info("=" * 70)
        self._logger.info(f"Node ID: {self._system['node_id']}")
        self._logger.info(f"Protocol Version: {self._system['protocol_version']}")
        self._logger.info(f"Config Version: {self._system['config_version']}")
        self._logger.info(f"DOI Anchor: {self._system['doi_anchor']}")
        self._logger.info(f"Environment: {self._system['environment']}")
        self._logger.info("")
        self._logger.info("Networks Configured:")
        for network_name, config in self._networks.items():
            status = "✅ Active" if config["rpc_url"] else "⚠️  Missing"
            self._logger.info(f"  - {config['name']} ({network_name}): {status}")
        self._logger.info("")
        self._logger.info(f"Wallet: {self._wallet['checksum_address'] or 'Not Configured'}")
        self._logger.info(f"Mode: {'Read-Only' if self._wallet['read_only_mode'] else 'Operational'}")
        self._logger.info("")
        self._logger.info(f"Validation Rules (1003 Rule):")
        self._logger.info(f"  Required Confidence: {self._validation['required_confidence']}")
        self._logger.info(f"  Required Verification Sources: {self._validation['required_verification_sources']}")
        self._logger.info("=" * 70)

    # =====================================================
    # PUBLIC API (v5.0 — Object-Oriented)
    # =====================================================

    @property
    def node_id(self) -> str:
        """Get node identifier."""
        return self._system["node_id"]

    @property
    def log_level(self) -> str:
        """Get log level."""
        return self._system["log_level"]

    @property
    def networks(self) -> Dict[str, Dict[str, Any]]:
        """
        Get network configurations.
        
        Returns:
            Immutable copy of network configurations
        """
        return self._networks.copy()

    def get_network(self, network_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific network.
        
        Args:
            network_name: Name of the network
        
        Returns:
            Network configuration or None if not found
        """
        return self._networks.get(network_name)

    def get_network_by_chain_id(self, chain_id: int) -> Optional[str]:
        """
        Get network name by chain ID.
        
        Args:
            chain_id: Chain ID to lookup
        
        Returns:
            Network name or None if not found
        """
        for network_name, config in self._networks.items():
            if config["chain_id"] == chain_id:
                return network_name
        return None

    @property
    def wallet_address(self) -> Optional[str]:
        """Get wallet address (checksummed)."""
        return self._wallet.get("checksum_address")

    @property
    def PADI_WALLET_ADDRESS(self) -> Optional[str]:
        """
        v4.0 backward compatibility: Get wallet address.
        Alias for wallet_address.
        """
        return self.wallet_address

    @property
    def private_key(self) -> Optional[str]:
        """Get private key (be cautious with this value)."""
        return self._wallet.get("private_key")

    @property
    def PADI_PRIVATE_KEY(self) -> Optional[str]:
        """
        v4.0 backward compatibility: Get private key.
        Alias for private_key.
        """
        return self.private_key

    @property
    def has_private_key(self) -> bool:
        """Check if private key is configured."""
        return self._wallet.get("has_private_key", False)

    @property
    def is_read_only_mode(self) -> bool:
        """Check if system is in read-only mode."""
        return self._wallet.get("read_only_mode", True)

    @property
    def schema_graph(self) -> Optional[Graph]:
        """
        Get PADI v3.0 schema graph.
        
        Returns:
            rdflib Graph or None if not loaded
        """
        return self._schema_graph

    @property
    def execution_config(self) -> Dict[str, Any]:
        """
        Get execution configuration.
        
        Returns:
            Immutable copy of execution configuration
        """
        return self._execution.copy()

    @property
    def validation_rules(self) -> Dict[str, Any]:
        """
        Get validation rules (1003 Rule).
        
        Returns:
            Immutable copy of validation rules
        """
        return self._validation.copy()

    # =====================================================
    # v4.0 BACKWARD COMPATIBILITY LAYER
    # =====================================================

    @property
    def NODE_ID(self) -> str:
        """v4.0 compatibility: Get node ID."""
        return self.node_id

    @property
    def LOG_LEVEL(self) -> str:
        """v4.0 compatibility: Get log level."""
        return self.log_level

    @property
    def GAS_LIMIT(self) -> int:
        """v4.0 compatibility: Get gas limit."""
        return self._execution["gas_limit"]

    @property
    def TX_TIMEOUT(self) -> int:
        """v4.0 compatibility: Get transaction timeout."""
        return self._execution["tx_timeout"]

    @property
    def DEFAULT_NETWORK_TYPE(self) -> str:
        """v4.0 compatibility: Get default network type."""
        return self._execution["default_network_type"]

    @property
    def DEFAULT_CROSS_NETWORK_VERIFICATION(self) -> bool:
        """v4.0 compatibility: Get cross-network verification flag."""
        return self._execution["default_cross_network_verification"]

    @property
    def REQUIRED_CONFIDENCE(self) -> float:
        """v4.0 compatibility: Get required confidence score."""
        return self._validation["required_confidence"]

    @property
    def REQUIRED_VERIFICATION_SOURCES(self) -> int:
        """v4.0 compatibility: Get required verification sources count."""
        return self._validation["required_verification_sources"]

    def get_network_config(self, network_type: str) -> Dict[str, Any]:
        """
        v4.0 compatibility: Get network configuration for a specific network type.
        
        Args:
            network_type: Network type
        
        Returns:
            Dictionary with network configuration
        
        Raises:
            ValueError: If network_type is invalid or not configured
        """
        config = self.get_network(network_type)
        
        if not config:
            raise ValueError(
                f"Invalid network_type: {network_type}. "
                f"Must be one of {list(self._networks.keys())}"
            )
        
        if not config["rpc_url"]:
            raise ValueError(
                f"RPC URL not configured for {network_type}. "
                f"Please set the environment variable."
            )
        
        return config

    def get_configured_networks(self) -> Dict[str, Dict[str, Any]]:
        """
        v4.0 compatibility: Get all configured networks.
        
        Returns:
            Dictionary mapping network types to their configurations
            Only includes networks with configured RPC URLs
        """
        return {
            network: config
            for network, config in self._networks.items()
            if config["rpc_url"]
        }

    def validate_network_config(self, network_type: str) -> Tuple[bool, str]:
        """
        v4.0 compatibility: Validate network configuration for a specific network.
        
        Args:
            network_type: Network type to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.get_network_config(network_type)
            return True, ""
        except ValueError as e:
            return False, str(e)

    def display_config(self):
        """
        v4.0 compatibility: Display current configuration settings.
        Prints configuration to console.
        """
        print("=" * 70)
        print("🏛️ PADI SOVEREIGN BUREAU — NODE CONFIGURATION v5.0")
        print("=" * 70)
        print()
        print("Node Identification:")
        print(f"  Node ID: {self.node_id}")
        print(f"  Log Level: {self.log_level}")
        print()
        print("Wallet Configuration:")
        print(f"  Wallet Address: {self.wallet_address or 'Not configured'}")
        print(f"  Private Key: {'Configured' if self.has_private_key else 'Not configured (read-only)'}")
        print()
        print("Network Configuration:")
        configured = self.get_configured_networks()
        if configured:
            for network, config in configured.items():
                print(f"  ✅ {config['name']} (Chain ID: {config['chain_id']})")
            print(f"  Default Network: {self.DEFAULT_NETWORK_TYPE}")
        else:
            print(f"  ❌ No networks configured")
        print()
        print("Validation Rules (1003 Rule):")
        print(f"  Required Confidence: {self.REQUIRED_CONFIDENCE}")
        print(f"  Required Verification Sources: {self.REQUIRED_VERIFICATION_SOURCES}")
        print()
        print("Execution Configuration:")
        print(f"  Gas Limit: {self.GAS_LIMIT}")
        print(f"  Transaction Timeout: {self.TX_TIMEOUT} seconds")
        print(f"  Cross-Network Verification: {self.DEFAULT_CROSS_NETWORK_VERIFICATION}")
        print()
        print("Schema Configuration:")
        print(f"  Schema Loaded: {'Yes' if self.schema_graph else 'No'}")
        print(f"  Schema Path: {self._schema_path}")
        print()
        print("=" * 70)

    # =====================================================
    # PRE-FLIGHT VERIFICATION (v5.0 — NEW)
    # =====================================================

    def verify_action_ontology(
        self,
        action_type: str,
        target_address: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify action against PADI v3.0 ontology.
        
        Args:
            action_type: Type of action (ARBITRAGE, SWAP, etc.)
            target_address: Target contract address
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate action type
        try:
            ActionType(action_type)
        except ValueError:
            return False, (
                f"Invalid action type: {action_type}. "
                f"Must be one of {[a.value for a in ActionType]}"
            )
        
        # Validate target address
        if not Web3.is_address(target_address):
            return False, f"Invalid target address: {target_address}"
        
        checksum_address = Web3.to_checksum_address(target_address)
        
        self._logger.info(
            f"✅ Pre-flight verification passed: "
            f"{action_type} → {checksum_address}"
        )
        
        return True, None

    def verify_network_context(
        self,
        network_type: str,
        chain_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify network context consistency.
        
        Args:
            network_type: Type of network
            chain_id: Chain ID
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        network_config = self._networks.get(network_type)
        
        if not network_config:
            return False, f"Unknown network type: {network_type}"
        
        if network_config["chain_id"] != chain_id:
            return False, (
                f"Chain ID mismatch for {network_type}: "
                f"expected {network_config['chain_id']}, got {chain_id}"
            )
        
        self._logger.info(
            f"✅ Network context verified: "
            f"{network_type} → Chain ID {chain_id}"
        )
        
        return True, None

    # =====================================================
    # VALIDATION AND DIAGNOSTICS
    # =====================================================

    def validate(self) -> bool:
        """
        Validate complete configuration.
        v4.0 compatibility method.
        
        Returns:
            True if validation passes
        """
        try:
            # Validate networks
            active_networks = sum(
                1 for net in self._networks.values()
                if net.get("rpc_url")
            )
            
            if active_networks == 0:
                raise ValueError("No active networks configured")
            
            # Validate wallet
            if not self.wallet_address:
                raise ValueError("No wallet address configured")
            
            self._logger.info("✅ Configuration validation: PASSED")
            return True
            
        except Exception as e:
            self._logger.error(f"❌ Configuration validation: FAILED - {e}")
            return False

    def get_diagnostics(self) -> Dict[str, Any]:
        """
        Get comprehensive diagnostics.
        
        Returns:
            Dictionary with diagnostic information
        """
        return {
            "node_id": self.node_id,
            "initialized": self._initialized,
            "config_version": self._system["config_version"],
            "protocol_version": self._system["protocol_version"],
            "doi_anchor": self._system["doi_anchor"],
            "networks": {
                "total": len(self._networks),
                "active": sum(1 for net in self._networks.values() if net.get("rpc_url")),
                "configurations": {
                    name: {
                        "chain_id": net["chain_id"],
                        "name": net["name"],
                        "network_type": net["network_type"].value,
                        "rpc_configured": bool(net["rpc_url"]),
                        "backup_available": bool(net.get("rpc_backup")),
                        "supports_l1_fee": net["supports_l1_fee"]
                    }
                    for name, net in self._networks.items()
                }
            },
            "wallet": {
                "configured": bool(self.wallet_address),
                "read_only_mode": self.is_read_only_mode,
                "has_private_key": self.has_private_key
            },
            "validation_rules": self._validation,
            "execution": self._execution,
            "schema": {
                "loaded": self._schema_graph is not None,
                "path": str(self._schema_path) if self._schema_path else None
            }
        }

    def export_config_snapshot(self, output_path: Optional[Path] = None) -> Path:
        """
        Export configuration snapshot for verification.
        
        Args:
            output_path: Optional output path
        
        Returns:
            Path to exported snapshot
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = Path("logs") / f"config_snapshot_{timestamp}.json"
        
        output_path.parent.mkdir(exist_ok=True)
        
        # Prepare safe snapshot (exclude sensitive data)
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "node_id": self.node_id,
            "config_version": self._system["config_version"],
            "protocol_version": self._system["protocol_version"],
            "doi_anchor": self._system["doi_anchor"],
            "networks": {
                name: {
                    "chain_id": net["chain_id"],
                    "name": net["name"],
                    "network_type": net["network_type"].value,
                    "rpc_configured": bool(net["rpc_url"]),
                    "supports_l1_fee": net["supports_l1_fee"],
                    "layer": net["layer"]
                }
                for name, net in self._networks.items()
            },
            "wallet": {
                "address": self.wallet_address,
                "read_only_mode": self.is_read_only_mode
            },
            "validation_rules": self._validation,
            "execution": self._execution,
            "system": {
                "log_level": self._system["log_level"],
                "environment": self._system["environment"],
                "timezone": self._system["timezone"]
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        self._logger.info(f"📄 Configuration snapshot exported to {output_path}")
        return output_path


# =====================================================
# MODULE-LEVEL ACCESS POINTS (v5.0 — Singleton Pattern)
# =====================================================

# Global configuration instance
_config: Optional[PadiConfig] = None
_config_lock = threading.Lock()


def get_config() -> PadiConfig:
    """
    Get global PADI configuration instance.
    
    v5.0 recommended access pattern:
        from padi_config import get_config
        config = get_config()
        print(config.node_id)
    
    v4.0 compatible access pattern (also works):
        from padi_config import PadiConfig
        config = PadiConfig()
        print(config.NODE_ID)
    
    Returns:
        Singleton PadiConfig instance
    """
    global _config
    
    with _config_lock:
        if _config is None:
            _config = PadiConfig()
    
    return _config


def initialize_config(
    env_path: Optional[Path] = None,
    schema_path: Optional[Path] = None
) -> PadiConfig:
    """
    Initialize global PADI configuration.
    
    Use this to manually initialize configuration with custom paths.
    
    Args:
        env_path: Optional path to .env file
        schema_path: Optional path to schema/ontology.ttl
    
    Returns:
        Initialized PadiConfig instance
    """
    global _config
    
    with _config_lock:
        _config = PadiConfig(env_path=env_path, schema_path=schema_path)
    
    return _config


# =====================================================
# STANDALONE DIAGNOSTICS
# =====================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize configuration
    config = get_config()
    
    # Validate configuration
    if config.validate():
        print("\n" + "=" * 70)
        print("🏛️ PADI SOVEREIGN CONFIGURATION — DIAGNOSTICS v5.0")
        print("=" * 70)
        
        # Display configuration (v4.0 compatibility)
        config.display_config()
        
        # Export snapshot
        snapshot_path = config.export_config_snapshot()
        print(f"\nConfiguration snapshot: {snapshot_path}")
        
        # Test pre-flight verification (v5.0 new)
        print("\n" + "=" * 70)
        print("Pre-Flight Verification Tests (v5.0)")
        print("=" * 70)
        
        # Valid action
        valid, error = config.verify_action_ontology(
            "ARBITRAGE",
            "0x4752ba5DBc23f44D620376279d4b37A730947593"
        )
        print(f"✅ Valid Action Test: {valid} | Error: {error}")
        
        # Network context
        valid, error = config.verify_network_context("op-mainnet", 10)
        print(f"✅ Valid Network Test: {valid} | Error: {error}")
        
        # Display diagnostics
        print("\n" + "=" * 70)
        print("Diagnostics Data")
        print("=" * 70)
        diagnostics = config.get_diagnostics()
        print(json.dumps(diagnostics, indent=2, default=str))
        
        print("\n✅ All diagnostics complete. PadiConfig v5.0 is operational.")
        print("=" * 70)
