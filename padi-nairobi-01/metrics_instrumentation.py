# =====================================================
# PADI EXECUTOR v5.3 — Metrics Instrumentation
# =====================================================
#
# This module provides Prometheus metrics instrumentation
# for the PADI Sovereign Bureau Executor system.
#
# Metrics Categories:
#   - Execution metrics (success/failure, duration)
#   - Audit confidence scores
#   - Ingestion latency
#   - Anomaly detection
#   - Circuit breaker status
#   - Gas optimization metrics
#
# Version: 5.3
# Node: Nairobi-01
# Timestamp: 2026-03-26 [EAT]

from prometheus_client import start_http_server, Counter, Histogram, Gauge, Summary, Info
import time
from functools import wraps
from typing import Callable, Any
import logging

# =====================================================
# Logger Configuration
# =====================================================
logger = logging.getLogger(__name__)

# =====================================================
# SYSTEM METRICS
# =====================================================

# System Information
SYSTEM_INFO = Info('padi_system_info', 'PADI System Information')
SYSTEM_INFO.info({
    'node': 'Nairobi-01',
    'region': 'east-africa',
    'environment': 'production',
    'version': '5.3'
})

# =====================================================
# EXECUTION METRICS
# =====================================================

# Execution counters
EXECUTION_SUCCESS_TOTAL = Counter(
    'padi_execution_success_total',
    'Total successful executions',
    ['network', 'action_type', 'gas_optimized']
)

EXECUTION_FAILURE_TOTAL = Counter(
    'padi_execution_failure_total',
    'Total failed executions',
    ['network', 'action_type', 'error_type']
)

# Execution duration histogram (in seconds)
EXECUTION_DURATION_SECONDS = Histogram(
    'padi_execution_duration_seconds',
    'Execution duration in seconds',
    ['network', 'action_type'],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0]
)

# Execution summary (for faster aggregation)
EXECUTION_SUMMARY = Summary(
    'padi_execution_summary_seconds',
    'Execution duration summary',
    ['network', 'action_type']
)

# =====================================================
# AUDIT METRICS
# =====================================================

# Audit confidence score gauge
AUDIT_CONFIDENCE_SCORE = Gauge(
    'padi_audit_confidence_score',
    'Current audit confidence score',
    ['network', 'audit_type']
)

# Audit results
AUDIT_PASS_TOTAL = Counter(
    'padi_audit_pass_total',
    'Total number of passed audits',
    ['network', 'audit_type']
)

AUDIT_FAIL_TOTAL = Counter(
    'padi_audit_fail_total',
    'Total number of failed audits',
    ['network', 'audit_type', 'severity']
)

# =====================================================
# INGESTION METRICS
# =====================================================

# Ingestion latency histogram (in seconds)
INGESTION_LATENCY_SECONDS = Histogram(
    'padi_ingestion_latency_seconds',
    'Ingestion pipeline latency in seconds',
    ['data_type', 'source'],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0]
)

# Ingestion throughput
INGESTION_RECORDS_TOTAL = Counter(
    'padi_ingestion_records_total',
    'Total number of records ingested',
    ['data_type', 'source', 'status']
)

# =====================================================
# ANOMALY DETECTION METRICS
# =====================================================

# Anomaly counter
ANOMALY_DETECTED_TOTAL = Counter(
    'padi_anomaly_detected_total',
    'Total anomalies detected',
    ['anomaly_type', 'severity', 'network']
)

# Anomaly score gauge
ANOMALY_SCORE = Gauge(
    'padi_anomaly_score',
    'Current anomaly score',
    ['anomaly_type', 'network']
)

# =====================================================
# CIRCUIT BREAKER METRICS
# =====================================================

# Circuit breaker state gauge
CIRCUIT_BREAKER_STATE = Gauge(
    'padi_circuit_breaker_state',
    'Circuit breaker state',
    ['network', 'operation']
)
# State values: 0 = closed, 0.5 = half-open, 1 = open

# Circuit breaker trip counter
CIRCUIT_BREAKER_TRIPPED_TOTAL = Counter(
    'padi_circuit_breaker_tripped_total',
    'Total number of circuit breaker trips',
    ['network', 'operation']
)

# Circuit breaker reset counter
CIRCUIT_BREAKER_RESET_TOTAL = Counter(
    'padi_circuit_breaker_reset_total',
    'Total number of circuit breaker resets',
    ['network', 'operation']
)

# =====================================================
# GAS OPTIMIZATION METRICS
# =====================================================

# Gas savings gauge (in Wei)
GAS_SAVINGS_WEI = Gauge(
    'padi_gas_savings_wei',
    'Accumulated gas savings in Wei',
    ['network', 'optimization_type']
)

# Gas price comparison
GAS_PRICE_CURRENT_WEI = Gauge(
    'padi_gas_price_current_wei',
    'Current gas price in Wei',
    ['network']
)

GAS_PRICE_SAVED_WEI = Gauge(
    'padi_gas_price_saved_wei',
    'Gas price saved per transaction in Wei',
    ['network', 'optimization_type']
)

# =====================================================
# NETWORK CONNECTION METRICS
# =====================================================

# Network connection status gauge
NETWORK_CONNECTION_STATUS = Gauge(
    'padi_network_connection_status',
    'Network connection status',
    ['network', 'chain_id']
)
# Status values: 0 = disconnected, 1 = connected

# RPC error counter
RPC_ERROR_TOTAL = Counter(
    'padi_rpc_error_total',
    'Total RPC errors',
    ['network', 'error_type', 'endpoint']
)

# =====================================================
# RESILIENCE METRICS
# =====================================================

# Retry counter
RETRY_TOTAL = Counter(
    'padi_retry_total',
    'Total number of retries',
    ['network', 'operation', 'reason']
)

# Fallback trigger counter
FALLBACK_TRIGGERED_TOTAL = Counter(
    'padi_fallback_triggered_total',
    'Total number of fallback activations',
    ['operation', 'from_provider', 'to_provider']
)

# Receipt tracking counter
RECEIPT_TRACKED_TOTAL = Counter(
    'padi_receipt_tracked_total',
    'Total number of transaction receipts tracked',
    ['network', 'status']
)

# =====================================================
# DECORATORS FOR AUTOMATIC METRICS COLLECTION
# =====================================================

def track_execution(network: str, action_type: str):
    """
    Decorator to track execution metrics.
    
    Args:
        network: The blockchain network (e.g., 'ethereum', 'polygon')
        action_type: The type of action (e.g., 'transaction', 'call')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            gas_optimized = kwargs.get('gas_optimized', False)
            
            try:
                result = func(*args, **kwargs)
                
                # Record success metrics
                EXECUTION_SUCCESS_TOTAL.labels(
                    network=network,
                    action_type=action_type,
                    gas_optimized=str(gas_optimized)
                ).inc()
                
                # Record duration
                duration = time.time() - start_time
                EXECUTION_DURATION_SECONDS.labels(
                    network=network,
                    action_type=action_type
                ).observe(duration)
                
                EXECUTION_SUMMARY.labels(
                    network=network,
                    action_type=action_type
                ).observe(duration)
                
                logger.info(f"Execution succeeded: {action_type} on {network} in {duration:.2f}s")
                return result
                
            except Exception as e:
                # Record failure metrics
                error_type = type(e).__name__
                EXECUTION_FAILURE_TOTAL.labels(
                    network=network,
                    action_type=action_type,
                    error_type=error_type
                ).inc()
                
                logger.error(f"Execution failed: {action_type} on {network} - {error_type}: {e}")
                raise
        
        return wrapper
    return decorator

def track_ingestion(data_type: str, source: str):
    """
    Decorator to track ingestion pipeline metrics.
    
    Args:
        data_type: The type of data being ingested (e.g., 'receipts', 'events')
        source: The source of the data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Record latency
                duration = time.time() - start_time
                INGESTION_LATENCY_SECONDS.labels(
                    data_type=data_type,
                    source=source
                ).observe(duration)
                
                # Record throughput (count records)
                if hasattr(result, '__len__'):
                    count = len(result)
                else:
                    count = 1
                
                INGESTION_RECORDS_TOTAL.labels(
                    data_type=data_type,
                    source=source,
                    status='success'
                ).inc(count)
                
                logger.info(f"Ingestion succeeded: {count} {data_type} records from {source} in {duration:.2f}s")
                return result
                
            except Exception as e:
                INGESTION_RECORDS_TOTAL.labels(
                    data_type=data_type,
                    source=source,
                    status='error'
                ).inc()
                logger.error(f"Ingestion failed: {data_type} from {source} - {e}")
                raise
        
        return wrapper
    return decorator

def track_audit(network: str, audit_type: str):
    """
    Decorator to track audit metrics.
    
    Args:
        network: The blockchain network
        audit_type: The type of audit being performed
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                result = func(*args, **kwargs)
                
                # Extract confidence score from result if available
                confidence_score = None
                if isinstance(result, dict):
                    confidence_score = result.get('confidence_score')
                elif hasattr(result, 'confidence_score'):
                    confidence_score = result.confidence_score
                
                if confidence_score is not None:
                    AUDIT_CONFIDENCE_SCORE.labels(
                        network=network,
                        audit_type=audit_type
                    ).set(confidence_score)
                
                # Record audit pass
                AUDIT_PASS_TOTAL.labels(
                    network=network,
                    audit_type=audit_type
                ).inc()
                
                logger.info(f"Audit passed: {audit_type} on {network} with confidence {confidence_score}")
                return result
                
            except Exception as e:
                # Record audit fail
                error_type = type(e).__name__
                severity = 'critical' if 'critical' in str(e).lower() else 'warning'
                
                AUDIT_FAIL_TOTAL.labels(
                    network=network,
                    audit_type=audit_type,
                    severity=severity
                ).inc()
                
                logger.error(f"Audit failed: {audit_type} on {network} - {error_type}: {e}")
                raise
        
        return wrapper
    return decorator


# =====================================================
# HELPER FUNCTIONS FOR MANUAL METRICS UPDATES
# =====================================================

def update_circuit_breaker_state(network: str, operation: str, state: str):
    """
    Update circuit breaker state gauge.
    
    Args:
        network: The blockchain network
        operation: The operation type
        state: The circuit breaker state ('closed', 'half_open', 'open')
    """
    state_values = {
        'closed': 0,
        'half_open': 0.5,
        'open': 1
    }
    value = state_values.get(state.lower(), 0)
    CIRCUIT_BREAKER_STATE.labels(network=network, operation=operation).set(value)
    logger.info(f"Circuit breaker state updated: {network}/{operation} = {state}")

def record_gas_savings(network: str, optimization_type: str, savings_wei: int):
    """
    Record gas savings.
    
    Args:
        network: The blockchain network
        optimization_type: The optimization strategy used
        savings_wei: Gas savings in Wei
    """
    GAS_SAVINGS_WEI.labels(network=network, optimization_type=optimization_type).inc(savings_wei)
    logger.info(f"Gas savings recorded: {savings_wei} Wei on {network} via {optimization_type}")

def update_anomaly_score(anomaly_type: str, network: str, score: float):
    """
    Update anomaly score gauge.
    
    Args:
        anomaly_type: The type of anomaly
        network: The blockchain network
        score: The anomaly score (0.0 to 1.0)
    """
    ANOMALY_SCORE.labels(anomaly_type=anomaly_type, network=network).set(score)
    logger.info(f"Anomaly score updated: {anomaly_type} on {network} = {score}")

def update_network_status(network: str, chain_id: str, status: bool):
    """
    Update network connection status.
    
    Args:
        network: The blockchain network
        chain_id: The chain ID
        status: Connection status (True = connected, False = disconnected)
    """
    value = 1 if status else 0
    NETWORK_CONNECTION_STATUS.labels(network=network, chain_id=chain_id).set(value)
    logger.info(f"Network status updated: {network} ({chain_id}) = {'connected' if status else 'disconnected'}")

def record_rpc_error(network: str, error_type: str, endpoint: str):
    """
    Record an RPC error.
    
    Args:
        network: The blockchain network
        error_type: The type of error
        endpoint: The RPC endpoint that failed
    """
    RPC_ERROR_TOTAL.labels(network=network, error_type=error_type, endpoint=endpoint).inc()
    logger.warning(f"RPC error recorded: {error_type} on {network} at {endpoint}")


# =====================================================
# SERVER INITIALIZATION
# =====================================================

def start_metrics_server(port: int = 8000):
    """
    Start the Prometheus metrics HTTP server.
    
    Args:
        port: The port to listen on (default: 8000)
    """
    start_http_server(port)
    logger.info(f"Prometheus metrics server started on port {port}")


# =====================================================
# EXAMPLE USAGE
# =====================================================

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start metrics server
    start_metrics_server(port=8000)
    
    # Example: Track execution
    @track_execution(network='ethereum', action_type='transaction')
    def mock_transaction():
        time.sleep(0.5)
        return {'success': True, 'tx_hash': '0x123...'}
    
    # Example: Track ingestion
    @track_ingestion(data_type='receipts', source='ethereum_mainnet')
    def mock_ingestion():
        time.sleep(0.2)
        return [{'tx_hash': '0x123...'}, {'tx_hash': '0x456...'}]
    
    # Example: Track audit
    @track_audit(network='ethereum', audit_type='security')
    def mock_audit():
        time.sleep(0.1)
        return {'confidence_score': 0.95, 'passed': True}
    
    # Run examples
    mock_transaction()
    mock_ingestion()
    mock_audit()
    
    # Example: Manual metric updates
    update_circuit_breaker_state('ethereium', 'transaction', 'open')
    record_gas_savings('ethereum', 'dynamic', 25000000000)
    update_anomaly_score('gas_spike', 'ethereum', 0.75)
    update_network_status('ethereum', '1', True)
    record_rpc_error('ethereum', 'timeout', 'https://mainnet.infura.io/v3/xxx')
    
    print("Metrics running... Press Ctrl+C to stop")
    while True:
        time.sleep(1)
