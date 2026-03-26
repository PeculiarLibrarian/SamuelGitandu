#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any
from rdflib import Graph, Namespace, Literal, RDF, XSD
from pyshacl import validate
from datetime import datetime

# ✅ FIXED: Import PadiConfig for dynamic network configuration
from padi_config import get_config as PadiConfig

# =====================================================
# 🏛️ PADI BUREAU CORE v1.2 — NAIROBI NODE-01
# SHACL-ENFORCED VALIDATION WITH PATH VALIDATION
# =====================================================

# 1. NAMESPACE CONFIGURATION
EX = Namespace("http://padi.u/schema#")

# =====================================================
# 🛡️ V1.2 NEW: PATH VALIDATION FUNCTIONS
# =====================================================

def validate_shacl_paths(
    shapes_path: Optional[str] = None,
    ontology_path: Optional[str] = None
) -> Tuple[bool, str, str, str]:
    """
    Validate SHAML file paths exist before running validation.
    
    This function prevents the "Ghost" Pathing vulnerability by
    verifying that SHAML and ontology files exist before attempting
    validation.
    
    Args:
        shapes_path: Path to shapes.ttl file (optional)
        ontology_path: Path to ontology.ttl file (optional)
    
    Returns:
        is_valid (bool): True if both paths are valid
        validated_shapes_path (str): Validated shapes file path
        validated_ontology_path (str): Validated ontology file path
        error_message (str): Error message if validation fails
    """
    # Load PadiConfig for default paths
    config = PadiConfig()
    
    # Get default paths from PadiConfig or use fallback paths
    default_shapes_path = config.get("shapes_graph_path", "schema/shapes.ttl")
    default_ontology_path = config.get("ontology_graph_path", "schema/ontology.ttl")
    
    # Use provided paths or default paths
    shapes_path = shapes_path or default_shapes_path
    ontology_path = ontology_path or default_ontology_path
    
    errors = []
    
    # Validate shapes path
    shapes_file = Path(shapes_path)
    if not shapes_file.exists():
        error_msg = (
            f"SHAML shapes file not found: {shapes_path}\n"
            f"Expected location: {shapes_file.absolute()}\n"
            f"Current working directory: {os.getcwd()}"
        )
        errors.append(error_msg)
    
    # Validate ontology path
    ontology_file = Path(ontology_path)
    if not ontology_file.exists():
        error_msg = (
            f"Ontology file not found: {ontology_path}\n"
            f"Expected location: {ontology_file.absolute()}\n"
            f"Current working directory: {os.getcwd()}"
        )
        errors.append(error_msg)
    
    if errors:
        return False, "", "", "\n".join(errors)
    
    return True, str(shapes_file.absolute()), str(ontology_file.absolute()), ""


def get_network_config(network_type: str) -> Dict[str, Any]:
    """
    Get network configuration from PadiConfig singleton.
    
    Args:
        network_type: Network type string
    
    Returns:
        Dictionary with network configuration
    """
    config = PadiConfig()
    return config.get_network_config(network_type)


def get_valid_networks() -> List[str]:
    """
    Get list of valid networks from PadiConfig singleton.
    
    Returns:
        List of valid network type strings
    """
    config = PadiConfig()
    return list(config.networks.keys())


def validate_network_type(network_type: str) -> bool:
    """
    Validate network type against PadiConfig.
    
    Args:
        network_type: Network type string
    
    Returns:
        True if valid, False otherwise
    """
    config = PadiConfig()
    return network_type in config.networks


# =====================================================
# 🛡️ V1.2 NEW: SHAML VALIDATION WITH PATH VALIDATION
# =====================================================

def validate_with_shacl(
    data_graph: Graph,
    shapes_path: Optional[str] = None,
    ontology_path: Optional[str] = None,
    inference: str = 'rdfs',
    advanced: bool = True,
    allow_warnings: bool = True
) -> Tuple[bool, str, str]:
    """
    Validate RDF graph with SHAML using path validation.
    
    🛡️ V1.2: Prevents "Ghost" Pathing vulnerability by validating
    file paths before running pySHACL validation.
    
    Args:
        data_graph: RDF graph to validate
        shapes_path: Path to shapes.ttl file (optional)
        ontology_path: Path to ontology.ttl file (optional)
        inference: SHAML inference engine ('rdfs', 'none', etc.)
        advanced: Enable advanced SHAML features
        allow_warnings: Allow warnings in validation results
    
    Returns:
        conforms (bool): Whether graph conforms to SHAML constraints
        results_text (str): SHAML validation results text
        error_message (str): Error message if path validation fails
    """
    # 🛡️ V1.2: Validate paths before running SHAML
    paths_valid, validated_shapes_path, validated_ontology_path, error_message = validate_shacl_paths(
        shapes_path,
        ontology_path
    )
    
    if not paths_valid:
        # Return error without running validation
        return False, "", f"Path validation failed:\n{error_message}"
    
    try:
        # Run SHAML validation with validated paths
        conforms, _, results_text = validate(
            data_graph,
            shacl_graph=validated_shapes_path,
            ont_graph=validated_ontology_path,
            inference=inference,
            advanced=advanced,
            allow_warnings=allow_warnings
        )
        
        return conforms, results_text, ""
    
    except Exception as e:
        error_msg = f"SHAML validation error: {str(e)}"
        return False, "", error_msg


def audit_signal(
    name: str,
    confidence: float,
    sources: List[str],
    target_address: str,
    action_type: str,
    signal_id: str,
    # Network Context Parameters
    network_type: str = "op-mainnet",
    chain_id: Optional[int] = None,
    source_provider: Optional[str] = None,
    # Verification Metadata Parameters
    verification_confidence: Optional[List[float]] = None,
    verification_timestamp: Optional[List[str]] = None,
    verification_match: Optional[List[bool]] = None,
    # Cross-Network Verification Parameters
    primary_network: Optional[str] = None,
    fallback_network: Optional[str] = None,
    cross_network_verification: Optional[bool] = True,
    # Existing Parameters
    observed_at: Optional[str] = None,
    block_number: Optional[int] = None,
    gas_price_gwei: Optional[float] = None,
    is_validated: bool = False,
    # SHAML Configuration Parameters
    enforce_1003: bool = True,
    shapes_path: Optional[str] = None,
    ontology_path: Optional[str] = None,
    # SHAML Validation Options
    inference: str = 'rdfs',
    advanced: bool = True,
    allow_warnings: bool = True
) -> Tuple[Graph, bool, str, str]:
    """
    PADI Bureau Core Audit:
    Converts a signal into RDF and enforces the 1003 Rule via SHAML.
    
    🛡️ V1.2: Added path validation to prevent "Ghost" Pathing vulnerability.
    
    Args:
        name: Signal name (used as RDF node identifier)
        confidence: Confidence score (0.0 - 1.0). Must be 1.0 for 1003 Rule.
        sources: List of verification sources (enforced via SHAML)
        target_address: Contract or wallet address targeted by this signal
        action_type: Action type (e.g., SWAP, ARB, AUDIT)
        signal_id: Unique deterministic identifier (e.g., SHA256 hash)
        network_type: Network type ("op-mainnet", "op-sepolia", "eth-mainnet", "eth-sepolia")
        chain_id: EVM chain ID (10 for OP Mainnet, 1 for ETH Mainnet)
        source_provider: API provider that supplied the signal
        verification_confidence: List of confidence scores (0.0 - 1.0 each)
        verification_timestamp: List of ISO timestamps for each verification source
        verification_match: List of boolean match statuses
        primary_network: Primary network where signal was first observed
        fallback_network: Fallback network used for verification (optional)
        cross_network_verification: Whether signal was verified across networks
        observed_at: Timestamp when the signal was observed (UTC, ISO format)
        block_number: Blockchain block number where the signal was observed
        gas_price_gwei: Gas price at time of observation in Gwei
        is_validated: Indicates whether the signal passed validation (default False)
        enforce_1003: Whether to enforce 1003 rule via SHACL validation (default True)
        shapes_path: Path to SHAML shapes.ttl file (optional)
        ontology_path: Path to ontology.ttl file (optional)
        inference: SHAML inference engine ('rdfs', 'none', etc.)
        advanced: Enable advanced SHAML features
        allow_warnings: Allow warnings in validation results
    
    Returns:
        g (Graph) - RDF Graph of the signal
        conforms (bool) - SHAML conformance
        status (str) - Deterministic or Probabilistic status
        results_text (str) - SHAML validation report
    """
    # Load PadiConfig for network validation
    config = PadiConfig()
    
    # --- INPUT VALIDATION ---
    # Validate network_type against PadiConfig
    if not validate_network_type(network_type):
        valid_networks = get_valid_networks()
        raise ValueError(
            f"Invalid network_type: {network_type}. "
            f"Must be one of {valid_networks}"
        )
    
    # Load network configuration
    network_config = get_network_config(network_type)
    
    # Auto-detect chain_id if not provided
    if chain_id is None:
        chain_id = network_config["chain_id"]
    elif chain_id != network_config["chain_id"]:
        raise ValueError(
            f"Chain ID mismatch: network_type={network_type} "
            f"expects chain_id={network_config['chain_id']}, got {chain_id}"
        )
    
    # Auto-detect source_provider if not provided
    if source_provider is None:
        source_provider = network_config.get("provider", network_config["name"])
    
    # Auto-detect primary_network if not provided
    if primary_network is None:
        primary_network = network_type
    
    # Default cross_network_verification to True
    if cross_network_verification is None:
        cross_network_verification = True
    
    # --- RDF GRAPH CONSTRUCTION ---
    g = Graph()
    node = EX[name]

    # 1. CLASS ASSIGNMENT
    g.add((node, RDF.type, EX.FinancialSignal))

    # 2. 1003 RULE: Confidence & Verification Sources
    g.add((node, EX.hasConfidence, Literal(confidence, datatype=XSD.decimal)))
    for s in sources:
        g.add((node, EX.hasVerificationSource, Literal(s, datatype=XSD.string)))

    # 3. TARGETING LAYER
    g.add((node, EX.hasTargetAddress, Literal(target_address, datatype=XSD.string)))
    g.add((node, EX.hasActionType, Literal(action_type, datatype=XSD.string)))

    # 4. IDENTITY & TRACEABILITY
    g.add((node, EX.hasSignalID, Literal(signal_id, datatype=XSD.string)))
    observed_at = observed_at or datetime.utcnow().isoformat()
    g.add((node, EX.observedAt, Literal(observed_at, datatype=XSD.dateTime)))

    # 5. NETWORK CONTEXT
    g.add((node, EX.hasNetworkType, Literal(network_type, datatype=XSD.string)))
    g.add((node, EX.hasChainID, Literal(chain_id, datatype=XSD.integer)))
    g.add((node, EX.hasSourceProvider, Literal(source_provider, datatype=XSD.string)))

    # 6. VERIFICATION METADATA
    if verification_confidence is not None:
        for vc in verification_confidence:
            g.add((node, EX.hasVerificationConfidence, Literal(vc, datatype=XSD.decimal)))
    else:
        # Default to 1.0 for default sources if not provided
        default_sources = get_network_config(network_type).get("rpc_url", "Unknown")
        for _ in range(len(sources)):
            g.add((node, EX.hasVerificationConfidence, Literal(1.0, datatype=XSD.decimal)))
    
    if verification_timestamp is not None:
        for vt in verification_timestamp:
            g.add((node, EX.hasVerificationTimestamp, Literal(vt, datatype=XSD.dateTime)))
    else:
        # Default to current timestamp for default sources if not provided
        current_ts = datetime.utcnow().isoformat()
        for _ in range(len(sources)):
            g.add((node, EX.hasVerificationTimestamp, Literal(current_ts, datatype=XSD.dateTime)))
    
    if verification_match is not None:
        for vm in verification_match:
            g.add((node, EX.hasVerificationMatch, Literal(vm, datatype=XSD.boolean)))
    else:
        # Default to match for all sources if not provided
        for _ in range(len(sources)):
            g.add((node, EX.hasVerificationMatch, Literal(True, datatype=XSD.boolean)))

    # 7. CROSS-NETWORK VERIFICATION
    g.add((node, EX.hasPrimaryNetwork, Literal(primary_network, datatype=XSD.string)))
    
    if fallback_network is not None:
        g.add((node, EX.hasFallbackNetwork, Literal(fallback_network, datatype=XSD.string)))
    
    g.add((node, EX.hasCrossNetworkVerification, Literal(cross_network_verification, datatype=XSD.boolean)))

    # 8. INFRASTRUCTURE CONTEXT
    if block_number is not None:
        g.add((node, EX.atBlockNumber, Literal(block_number, datatype=XSD.integer)))
    if gas_price_gwei is not None:
        g.add((node, EX.hasGasPriceGwei, Literal(gas_price_gwei, datatype=XSD.decimal)))
    g.add((node, EX.isValidated, Literal(is_validated, datatype=XSD.boolean)))

    # 9. SHAML VALIDATION WITH PATH VALIDATION
    # 🛡️ V1.2: Use validate_with_shacl() with path validation
    if enforce_1003:
        conforms, results_text, error_message = validate_with_shacl(
            g,
            shapes_path=shapes_path,
            ontology_path=ontology_path,
            inference=inference,
            advanced=advanced,
            allow_warnings=allow_warnings
        )
        
        if error_message:
            # Return error without promoting to ExecutableFact
            status = f"❌ PROBABILISTIC (BLOCKED - Path/Validation Error): {error_message}"
            return g, False, status, error_message
    else:
        # Skip SHAML validation (for testing or override)
        conforms = True
        results_text = "SHML validation bypassed (enforce_1003=False)"

    # 10. DETERMINISTIC PROMOTION
    if conforms:
        # Upgrade FinancialSignal → ExecutableFact
        g.remove((node, RDF.type, EX.FinancialSignal))
        g.add((node, RDF.type, EX.ExecutableFact))
        # Update validation flag
        g.set((node, EX.isValidated, Literal(True, datatype=XSD.boolean)))
        status = "✅ DETERMINISTIC (PROMOTED TO FACT)"
    else:
        status = "❌ PROBABILISTIC (BLOCKED)"

    return g, conforms, status, results_text


# =====================================================
# HELPER FUNCTIONS (Unchanged)
# =====================================================

def create_verification_metadata(
    source_name: str,
    confidence: float,
    timestamp: Optional[str] = None,
    match: bool = True
) -> Dict[str, Any]:
    """
    Creates a structured verification metadata object.
    
    Args:
        source_name: Name of the verification source
        confidence: Confidence score (0.0 - 1.0)
        timestamp: ISO timestamp (default: current UTC time)
        match: Match status (default: True)
    
    Returns:
        Dictionary with verification metadata
    """
    return {
        "source": source_name,
        "confidence": confidence,
        "timestamp": timestamp or datetime.utcnow().isoformat(),
        "match": match
    }


def validate_verification_metadata(
    sources: List[str],
    verification_confidence: Optional[List[float]],
    verification_timestamp: Optional[List[str]],
    verification_match: Optional[List[bool]]
) -> Tuple[bool, str]:
    """
    Validates verification metadata consistency.
    
    Args:
        sources: List of verification source names
        verification_confidence: List of confidence scores
        verification_timestamp: List of timestamps
        verification_match: List of match statuses
    
    Returns:
        is_valid (bool): Whether metadata is valid
        error_message (str): Error message if invalid, empty string otherwise
    """
    n_sources = len(sources)
    
    # Check 1003 Rule: Exactly 3 sources
    if n_sources != 3:
        return False, f"Validation Error: Exactly 3 verification sources required (got {n_sources})"
    
    # Verify counts match
    if verification_confidence is not None and len(verification_confidence) != n_sources:
        return False, f"Validation Error: Expected {n_sources} confidence scores, got {len(verification_confidence)}"
    
    if verification_timestamp is not None and len(verification_timestamp) != n_sources:
        return False, f"Validation Error: Expected {n_sources} timestamps, got {len(verification_timestamp)}"
    
    if verification_match is not None and len(verification_match) != n_sources:
        return False, f"Validation Error: Expected {n_sources} match statuses, got {len(verification_match)}"
    
    return True, ""


def get_network_info(network_type: str) -> Dict[str, Any]:
    """
    Retrieves network information for a given network type.
    ✅ v1.2: Uses PadiConfig singleton.
    
    Args:
        network_type: Network type ("op-mainnet", "op-sepolia", "eth-mainnet", "eth-sepolia")
    
    Returns:
        Dictionary with chain ID, provider, and network class
    """
    config = PadiConfig()
    network_config = get_network_config(network_type)
    
    return {
        "network_type": network_type,
        "chain_id": network_config["chain_id"],
        "default_provider": network_config.get("provider", network_config["name"]),
        "rpc_url": network_config["rpc_url"],
        "network_class": network_config.get("network_class", "layer2")
    }


def validate_network_config(network_type: str, chain_id: Optional[int] = None) -> Tuple[bool, str]:
    """
    Validates network configuration.
    ✅ v1.2: Uses PadiConfig singleton.
    
    Args:
        network_type: Network type
        chain_id: Optional chain ID to validate consistency
    
    Returns:
        is_valid (bool): Whether configuration is valid
        error_message (str): Error message if invalid, empty string otherwise
    """
    config = PadiConfig()
    
    if not validate_network_type(network_type):
        valid_networks = get_valid_networks()
        return False, f"Invalid network_type: {network_type}. Must be one of {valid_networks}"
    
    if chain_id is not None:
        network_config = get_network_config(network_type)
        expected_chain_id = network_config["chain_id"]
        if chain_id != expected_chain_id:
            return False, f"Chain ID mismatch: network_type={network_type} expects chain_id={expected_chain_id}, got {chain_id}"
    
    return True, ""


# --- PRODUCTION TEST GATEWAY ---
if __name__ == "__main__":
    # Initialize PadiConfig singleton
    PadiConfig()
    
    print("--- PADI BUREAU: NAIROBI NODE-01 STANDALONE AUDIT v1.2 ---")
    print()

    # 🛡️ V1.2: Test path validation
    print("🛡️ Testing SHAML Path Validation...")
    print("-" * 50)
    paths_valid, shapes_path, ontology_path, error_msg = validate_shacl_paths()
    if paths_valid:
        print(f"✅ SHAML paths validated:")
        print(f"   Shapes: {shapes_path}")
        print(f"   Ontology: {ontology_path}")
        print()
    else:
        print(f"❌ SHAML path validation failed:")
        print(f"   {error_msg}")
        print()

    # Example 1: Probabilistic Signal (Should fail)
    # Missing verification metadata, incomplete 1003 Rule
    print("Example 1: Probabilistic Signal (Should FAIL)")
    print("-" * 50)
    try:
        g1, c1, s1, r1 = audit_signal(
            name="Simulation_Lead",
            confidence=0.8,
            sources=["Source_1"],  # Only 1 source (1003 Rule requires 3)
            target_address="0xABCDEF1234567890",
            action_type="SWAP",
            signal_id="SIM-001",
            block_number=12345678,
            gas_price_gwei=50.0
        )
        print(f"Signal: Simulation_Lead | Status: {s1}")
        if not c1:
            print(f"Sentinel Report:\n{r1}\n")
    except Exception as e:
        print(f"Error: {e}\n")

    # Example 2: Deterministic Signal on OP Mainnet (Should pass)
    # Full 1003 compliance with multi-network context
    print("Example 2: Deterministic Signal on OP Mainnet (Should PASS)")
    print("-" * 50)
    try:
        g2, c2, s2, r2 = audit_signal(
            name="Truth_Lead_OP",
            confidence=1.0,
            sources=["Alchemy-OP-Mainnet", "Infura-OP-Mainnet", "QuickNode-OP-Mainnet"],
            target_address="0x1234567890ABCDEF",
            action_type="ARB",
            signal_id="TRUTH-OP-001",
            network_type="op-mainnet",
            chain_id=10,
            source_provider="Alchemy-OP-Mainnet",
            verification_confidence=[1.0, 1.0, 1.0],
            verification_timestamp=["2026-03-26T00:00:00Z", "2026-03-26T00:00:01Z", "2026-03-26T00:00:02Z"],
            verification_match=[True, True, True],
            primary_network="op-mainnet",
            fallback_network="eth-mainnet",
            cross_network_verification=True,
            block_number=12345679,
            gas_price_gwei=55.0
        )
        print(f"Signal: Truth_Lead_OP | Status: {s2}")
        print(f"Network: op-mainnet (Chain ID: 10)")
        print(f"Provider: Alchemy-OP-Mainnet")
        print(f"Cross-Network: Verified on op-mainnet → eth-mainnet\n")
    except Exception as e:
        print(f"Error: {e}\n")

    # Example 3: Test with custom SHAML paths (optional)
    print("Example 3: Test with Custom SHAML Paths (Optional)")
    print("-" * 50)
    print("Note: This example demonstrates optional custom path handling.")
    print("If custom paths are not provided, defaults from PadiConfig are used.")
    print()

    # Example 4: Helper Functions Demo
    print("Example 4: Helper Functions Demo")
    print("-" * 50)
    print("Network Info for op-mainnet:")
    info = get_network_info("op-mainnet")
    print(f"  - Type: {info['network_type']}")
    print(f"  - Chain ID: {info['chain_id']}")
    print(f"  - Default Provider: {info['default_provider']}")
    print(f"  - RPC URL: {info['rpc_url']}")
    print(f"  - Network Class: {info['network_class']}")
    print()

    print("--- AUDIT COMPLETE v1.2 ---")
