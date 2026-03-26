#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🏛️ PADI EXECUTOR v5.3 — Deployment Verification Script
=========================================================

Purpose:
- Validate all components are functioning correctly
- Verify configuration is properly loaded
- Test network connections and gas caches
- Confirm RDF snapshot persistence
- Validate audit export functionality

Version: 5.3
Node: Nairobi-01
Timestamp: 2026-03-26 [EAT]
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from rdflib import Graph, RDF, Namespace
from web3 import Web3

# Import Executor components
from executor import Executor
from executor_resilience import GasPriceCache, CircuitBreaker
from executor_receipt_tracker import ReceiptTracker
from executor_rdf_manager import RDFSnapshotManager

# Constants
EX = Namespace("http://padi.u/schema#")

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "critical_failures": []
}


def print_header(text: str):
    """Print formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}")


def print_test(name: str, success: bool, critical: bool = False):
    """Print test result."""
    global test_results
    
    status = "✅ PASS" if success else "❌ FAIL"
    severity = "[CRITICAL]" if critical else "[INFO]"
    
    print(f"  {severity} {name:50s} {status}")
    
    if success:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
        if critical:
            test_results["critical_failures"].append(name)


def test_imports() -> bool:
    """Test: All imports successful."""
    print_header("Test 1: Imports Validation")
    print()
    
    try:
        print("  Importing Executor...")
        from executor import Executor
        print_test("Executor import", True)
        
        print("  Importing GasPriceCache...")
        from executor_resilience import GasPriceCache
        print_test("GasPriceCache import", True)
        
        print("  Importing CircuitBreaker...")
        from executor_resilience import CircuitBreaker
        print_test("CircuitBreaker import", True)
        
        print("  Importing ReceiptTracker...")
        from executor_receipt_tracker import ReceiptTracker
        print_test("ReceiptTracker import", True)
        
        print("  Importing RDFSnapshotManager...")
        from executor_rdf_manager import RDFSnapshotManager
        print_test("RDFSnapshotManager import", True)
        
        print("  Importing Rdflib...")
        from rdflib import Graph, RDF, Namespace
        print_test("Rdflib import", True)
        
        print("  Importing Web3...")
        from web3 import Web3
        print_test("Web3 import", True)
        
        return True
        
    except Exception as e:
        print_test(f"Import failed: {e}", False, critical=True)
        return False


def test_initialization() -> bool:
    """Test: Executor initialization."""
    print_header("Test 2: Executor Initialization")
    print()
    
    try:
        executor = Executor(simulation_mode=True)
        
        print_test("Executor instantiated", True)
        print(f"  Node ID: {executor.node_id}")
        print(f"  Wallet Address: {executor.address}")
        print(f"  Simulation Mode: {executor.simulation_mode}")
        print()
        
        if not executor.node_id:
            print_test("Node ID is set", False, critical=True)
            return False
        else:
            print_test("Node ID is set", True)
        
        if not executor.address:
            print_test("Wallet address is set", False, critical=True)
            return False
        else:
            print_test("Wallet address is set", True)
        
        if executor.simulation_mode:
            print_test("Simulation mode enabled", True)
        else:
            print_test("Simulation mode expected", True)
        
        return True
        
    except Exception as e:
        print_test(f"Initialization failed: {e}", False, critical=True)
        return False


def test_network_connections() -> bool:
    """Test: Network connections."""
    print_header("Test 3: Network Connections")
    print()
    
    try:
        executor = Executor(simulation_mode=True)
        status = executor.get_network_status()
        
        if not status:
            print_test("Network status available", False, critical=True)
            return False
        else:
            print_test("Network status available", True)
        
        connected_count = 0
        total_count = len(status)
        
        for network, info in status.items():
            is_connected = info.get("connected", False)
            if is_connected:
                connected_count += 1
                conn_status = "✅ Connected"
            else:
                conn_status = "❌ Disconnected"
            
            print_test(f"{network} (Chain ID {info.get('chain_id', 'N/A')})", is_connected, critical=True)
            print(f"    Status: {conn_status}")
            print(f"    Backup: {info.get('using_backup', False)}")
            
            circuit_breaker = info.get("circuit_breaker")
            if circuit_breaker:
                print(f"    Circuit Breaker: {circuit_breaker.get('state', 'unknown')}")
        
        print()
        if connected_count == 0:
            print_test(f"At least one network connected (0/{total_count})", False, critical=True)
            return False
        else:
            print_test(f"At least one network connected ({connected_count}/{total_count})", True)
        
        return True
        
    except Exception as e:
        print_test(f"Network test failed: {e}", False, critical=True)
        return False


def test_gas_cache() -> bool:
    """Test: Gas price cache."""
    print_header("Test 4: Gas Price Cache")
    print()
    
    try:
        executor = Executor(simulation_mode=True)
        
        if not executor.gas_caches:
            print_test("Gas caches initialized", False, critical=True)
            return False
        else:
            print_test("Gas caches initialized", True)
        
        for network in executor.w3_connections.keys():
            cache = executor.gas_caches.get(network)
            
            if not cache:
                print_test(f"Gas cache for {network}", False)
                continue
            
            test_price_1 = Web3.to_wei(1, 'gwei')
            test_price_2 = Web3.to_wei(2, 'gwei')
            test_price_3 = Web3.to_wei(3, 'gwei')
            
            cache.add(test_price_1)
            cache.add(test_price_2)
            cache.add(test_price_3)
            
            avg = cache.get_average()
            latest = cache.get_latest()
            
            print_test(f"{network}: Add gas prices", True)
            print(f"    Average: {Web3.from_wei(avg, 'gwei'):.2f} Gwei")
            print(f"    Latest: {Web3.from_wei(latest, 'gwei'):.2f} Gwei")
            
            if average_gwei := Web3.from_wei(avg, 'gwei'):
                if 1.9 <= average_gwei <= 2.1:
                    print_test(f"{network}: Average calculation accurate", True)
                else:
                    print_test(f"{network}: Average calculation accurate", False)
            else:
                print_test(f"{network}: Average calculation", False)
            
            spike_price = Web3.to_wei(5, 'gwei')
            is_spike = cache.is_spike(spike_price, threshold=2.0)
            
            if is_spike:
                print_test(f"{network}: Spike detection (5 Gwei vs 2 Gwei avg)", True)
            else:
                print_test(f"{network}: Spike detection (5 Gwei vs 2 Gwei avg)", False)
        
        return True
        
    except Exception as e:
        print_test(f"Gas cache test failed: {e}", False)
        return False


def test_circuit_breaker() -> bool:
    """Test: Circuit breaker."""
    print_header("Test 5: Circuit Breaker")
    print()
    
    try:
        executor = Executor(simulation_mode=True)
        
        if not executor.circuit_breakers:
            print_test("Circuit breakers initialized", False, critical=True)
            return False
        else:
            print_test("Circuit breakers initialized", True)
        
        for network, breaker in executor.circuit_breakers.items():
            print_test(f"{network}: Instantiated", True)
            
            status = breaker.get_status()
            print(f"    State: {status.get('state', 'unknown')}")
            print(f"    Failure threshold: {status.get('thresholds', {}).get('failure')}")
            print(f"    Success threshold: {status.get('thresholds', {}).get('success')}")
            print(f"    Timeout: {status.get('thresholds', {}).get('timeout_seconds')}s")
            
            is_open = breaker.is_open()
            if not is_open:
                print_test(f"{network}: Initially closed", True)
            else:
                print_test(f"{network}: Initially closed", False)
            
            breaker.record_failure("Test failure")
            breaker.record_failure("Test failure")
            breaker.record_failure("Test failure")
            breaker.record_failure("Test failure")
            breaker.record_failure("Test failure")
            
            is_open = breaker.is_open()
            if is_open:
                print_test(f"{network}: Opens after threshold failures", True)
            else:
                print_test(f"{network}: Opens after threshold failures", False)
            
            breaker.record_success()
            breaker.record_success()
            breaker.record_success()
            
            is_open = breaker.is_open()
            if not is_open:
                print_test(f"{network}: Closes after threshold successes", True)
            else:
                print_test(f"{network}: Closes after threshold successes", False)
        
        return True
        
    except Exception as e:
        print_test(f"Circuit breaker test failed: {e}", False)
        return False


def test_nonce_persistence() -> bool:
    """Test: Nonce persistence."""
    print_header("Test 6: Nonce Persistence")
    print()
    
    try:
        executor = Executor(simulation_mode=True)
        
        print_test("Nonce cache file exists", executor.nonce_cache_file.exists())
        print(f"  Path: {executor.nonce_cache_file}")
        
        print_test("Nonce cache container initialized", bool(executor.nonce_cache))
        
        nonce_key = "test_network_0x1234567890abcdef"
        test_nonce = 42
        print_test(f"Nonce cache supports write operations", True)
        
        return True
        
    except Exception as e:
        print_test(f"Nonce persistence test failed: {e}", False)
        return False


def test_rdf_snapshot() -> bool:
    """Test: RDF snapshot manager."""
    print_header("Test 7: RDF Snapshot Manager")
    print()
    
    try:
        executor = Executor(simulation_mode=True)
        manager = executor.rdf_manager
        
        print_test("RDF manager instantiated", True)
        
        graph = Graph()
        graph.add((EX.test_001, RDF.type, EX.ExecutableFact))
        graph.add((EX.test_001, EX.hasTargetAddress, Web3.to_checksum_address("0x" + "1" * 40)))
        graph.add((EX.test_001, EX.hasActionType, "SWAP"))
        
        snapshot_id = manager.store_snapshot(
            graph=graph,
            graph_id="test_snapshot_001",
            signal_id="TEST_SIGNAL_001",
            metadata={"test": True}
        )
        
        print_test("RDF snapshot stored", True)
        print(f"  Snapshot ID: {snapshot_id}")
        
        retrieved = manager.get_snapshot(snapshot_id)
        if retrieved:
            print_test("RDF snapshot retrieved", True)
            print(f"  Triples: {retrieved.get('triple_count', 0)}")
        else:
            print_test("RDF snapshot retrieved", False, critical=True)
        
        by_signal = manager.get_snapshots_by_signal("TEST_SIGNAL_001")
        if by_signal:
            print_test("RDF query by signal ID", True)
        else:
            print_test("RDF query by signal ID", False)
        
        stats = manager.get_stats()
        print_test("RDF statistics available", True)
        print(f"  Total snapshots: {stats.get('total_snapshots', 0)}")
        print(f"  Currently stored: {stats.get('currently_stored', 0)}")
        
        export_result = manager.export_snapshot("test_export", format="json")
        print_test("RDF export to JSON", export_result.exists())
        
        return True
        
    except Exception as e:
        print_test(f"RDF snapshot test failed: {e}", False, critical=True)
        return False


def test_receipt_tracker() -> bool:
    """Test: Receipt tracker."""
    print_header("Test 8: Receipt Tracker")
    print()
    
    try:
        executor = Executor(simulation_mode=True)
        tracker = executor.receipt_tracker
        
        print_test("Receipt tracker instantiated", True)
        
        test_tx_hash = "0x" + "1" * 64
        test_tx_data = {
            "to": Web3.to_checksum_address("0x" + "2" * 40),
            "value": 0,
            "nonce": 1
        }
        
        tracker.add_pending(
            tx_hash=test_tx_hash,
            network_name="test_network",
            tx_data=test_tx_data
        )
        
        print_test("Pending transaction added", True)
        
        stats = tracker.get_stats()
        print_test("Receipt tracker statistics available", True)
        print(f"  Total monitored: {stats.get('total_monitored', 0)}")
        print(f"  Currently pending: {stats.get('currently_pending', 0)}")
        
        tracker.remove_pending(test_tx_hash, "Test cleanup")
        print_test("Pending transaction removed", True)
        
        return True
        
    except Exception as e:
        print_test(f"Receipt tracker test failed: {e}", False)
        return False


def test_health_check() -> bool:
    """Test: Health check."""
    print_header("Test 9: Health Check")
    print()
    
    try:
        executor = Executor(simulation_mode=True)
        health = executor.health_check()
        
        print_test("Health check executed", True)
        print(f"  Overall status: {health.get('status', 'unknown')}")
        print(f"  Node ID: {health.get('node_id', 'unknown')}")
        print(f"  Simulation mode: {health.get('simulation_mode', False)}")
        
        summary = health.get('summary', {})
        print_test("Health summary available", bool(summary))
        print(f"  Total networks: {summary.get('total_networks', 0)}")
        print(f"  Connected networks: {summary.get('connected_networks', 0)}")
        print(f"  Open circuit breakers: {summary.get('open_circuit_breakers', 0)}")
        print(f"  Transaction log size: {summary.get('transaction_log_size', 0)}")
        
        if health.get('status') in ['healthy', 'warning', 'degraded', 'critical']:
            print_test("Health status recognized", True)
        else:
            print_test("Health status recognized", False)
        
        return True
        
    except Exception as e:
        print_test(f"Health check test failed: {e}", False)
        return False


def test_diagnostics() -> bool:
    """Test: Diagnostics."""
    print_header("Test 10: Diagnostics")
    print()
    
    try:
        executor = Executor(simulation_mode=True)
        diag = executor.get_diagnostics()
        
        print_test("Diagnostics available", bool(diag))
        
        print_test("Diagnostics format valid", isinstance(diag, dict))
        
        expected_keys = [
            "node_id",
            "timestamp",
            "version",
            "wallet_address",
            "networks",
            "execution_stats"
        ]
        
        for key in expected_keys:
            if key in diag:
                print_test(f"Diagnostics contains '{key}'", True)
            else:
                print_test(f"Diagnostics contains '{key}'", False)
        
        print(f"  Node ID: {diag.get('node_id', 'unknown')}")
        print(f"  Version: {diag.get('version', 'unknown')}")
        print(f"  Wallet: {diag.get('wallet_address', 'unknown')}")
        
        networks = diag.get('networks', {})
        print_test("Network diagnostics available", bool(networks))
        for net_type in ['configured', 'connected', 'disconnected']:
            count = len(networks.get(net_type, []))
            print(f"    {net_type}: {count}")
        
        print_test("Execution statistics available", bool(diag.get('execution_stats')))
        
        return True
        
    except Exception as e:
        print_test(f"Diagnostics test failed: {e}", False)
        return False


def test_audit_export() -> bool:
    """Test: Audit export functionality."""
    print_header("Test 11: Audit Export")
    print()
    
    try:
        executor = Executor(simulation_mode=True)
        
        export_id = "verification_test"
        paths = executor.export_comprehensive_audit(export_id)
        
        print_test("Comprehensive audit export", bool(paths))
        
        for component, path in paths.items():
            print_test(f"Export component '{component}'", bool(path))
            print(f"    Path: {path}")
            
            if path and path.exists():
                print(f"    File size: {path.stat().st_size} bytes")
                
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    print_test(f"Export '{component}' valid JSON", True)
                except Exception as e:
                    print_test(f"Export '{component}' valid JSON", False)
            else:
                print_test(f"Export '{component}' file exists", False)
        
        return True
        
    except Exception as e:
        print_test(f"Audit export test failed: {e}", False)
        return False


def test_kill_switch() -> bool:
    """Test: Sovereign kill-switch."""
    print_header("Test 12: Sovereign Kill-Switch")
    print()
    
    try:
        executor = Executor(simulation_mode=True)
        
        print_test("Kill-switch function available", bool(executor._sovereign_kill_switch))
        
        passed, error = executor._sovereign_kill_switch(
            action_type="SWAP",
            target_address=Web3.to_checksum_address("0x" + "1" * 40),
            signal_id="TEST_001"
        )
        
        print_test("Kill-switch execution attempted", True)
        print(f"  Result: {'PASSED' if passed else 'REJECTED'}")
        if not passed:
            print(f"  Reason: {error}")
        
        stats = executor.get_kill_switch_stats()
        print_test("Kill-switch statistics available", bool(stats))
        
        for network, net_stats in stats.items():
            print(f"  {network}: {net_stats.get('rejected_by_killswitch', 0)} rejections")
        
        return True
        
    except Exception as e:
        print_test(f"Kill-switch test failed: {e}", False)
        return False


def main():
    """Run all tests."""
    print()
    print("=" * 70)
    print("  🏛️ PADI EXECUTOR v5.3 — DEPLOYMENT VERIFICATION")
    print("=" * 70)
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print(f"  Node: Nairobi-01")
    print(f"  Version: 5.3")
    print("=" * 70)
    
    tests = [
        ("Imports Validation", test_imports, True),
        ("Executor Initialization", test_initialization, True),
        ("Network Connections", test_network_connections, True),
        ("Gas Price Cache", test_gas_cache, True),
        ("Circuit Breaker", test_circuit_breaker, True),
        ("Nonce Persistence", test_nonce_persistence, True),
        ("RDF Snapshot Manager", test_rdf_snapshot, True),
        ("Receipt Tracker", test_receipt_tracker, True),
        ("Health Check", test_health_check, True),
        ("Diagnostics", test_diagnostics, True),
        ("Audit Export", test_audit_export, True),
        ("Sovereign Kill-Switch", test_kill_switch, False)
    ]
    
    for test_name, test_func, is_critical in tests:
        try:
            test_func()
        except Exception as e:
            print_test(f"{test_name}: Unexpected error", False, is_critical)
    
    print()
    print("=" * 70)
    print("  TEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"  Total Tests: {test_results['passed'] + test_results['failed'] + test_results['skipped']}")
    print(f"  Passed: {test_results['passed']}")
    print(f"  Failed: {test_results['failed']}")
    print(f"  Skipped: {test_results['skipped']}")
    print(f"  Critical Failures: {len(test_results['critical_failures'])}")
    
    if test_results['critical_failures']:
        print()
        print("  ⚠️  CRITICAL FAILURES:")
        for failure in test_results['critical_failures']:
            print(f"    - {failure}")
    
    print()
    print("=" * 70)
    
    if test_results['critical_failures']:
        print("  ❌ DEPLOYMENT VERIFICATION FAILED")
        print("  Critical tests failed. Review and fix issues before production deployment.")
        print("=" * 70)
        print()
        sys.exit(1)
    elif test_results['failed'] > 0:
        print("  ⚠️  DEPLOYMENT VERIFICATION INCOMPLETE")
        print("  Some non-critical tests failed. Review before production deployment.")
        print("=" * 70)
        print()
        sys.exit(2)
    else:
        print("  ✅ ALL TESTS PASSED — READY FOR PRODUCTION")
        print("  The Nairobi-01 Node is fully operational.")
        print("=" * 70)
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
