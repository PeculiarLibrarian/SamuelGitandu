from rdflib import Graph, Namespace, Literal, RDF, XSD
from pyshacl import validate
from datetime import datetime

# 1. NAMESPACE CONFIGURATION
# Must match ontology.ttl and shapes.ttl exactly
EX = Namespace("http://padi.u/schema#")

def audit_signal(
    name,
    confidence,
    sources,
    target_address,
    action_type,
    signal_id,
    observed_at=None,
    block_number=None,
    gas_price_gwei=None,
    is_validated=False  # Default to False until SHACL validation
):
    """
    PADI Bureau Core Audit:
    Converts a signal into RDF and enforces the 1003 Rule via SHACL.
    
    Returns:
        g (Graph) - RDF Graph of the signal
        conforms (bool) - SHACL conformance
        status (str) - Deterministic or Probabilistic status
        results_text (str) - SHACL validation report
    """
    g = Graph()
    node = EX[name]

    # --- 1. CLASS ASSIGNMENT ---
    g.add((node, RDF.type, EX.FinancialSignal))  # Base class assignment

    # --- 2. 1003 RULE: Confidence & Verification Sources ---
    g.add((node, EX.hasConfidence, Literal(confidence, datatype=XSD.decimal)))
    for s in sources:
        g.add((node, EX.hasVerificationSource, Literal(s, datatype=XSD.string)))

    # --- 3. TARGETING LAYER (0 CONFLICT) ---
    g.add((node, EX.hasTargetAddress, Literal(target_address, datatype=XSD.string)))
    g.add((node, EX.hasActionType, Literal(action_type, datatype=XSD.string)))

    # --- 4. IDENTITY & TRACEABILITY ---
    g.add((node, EX.hasSignalID, Literal(signal_id, datatype=XSD.string)))
    observed_at = observed_at or datetime.utcnow().isoformat()
    g.add((node, EX.observedAt, Literal(observed_at, datatype=XSD.dateTime)))

    # --- 5. INFRASTRUCTURE CONTEXT (BASE L2) ---
    if block_number is not None:
        g.add((node, EX.atBlockNumber, Literal(block_number, datatype=XSD.integer)))
    if gas_price_gwei is not None:
        g.add((node, EX.hasGasPriceGwei, Literal(gas_price_gwei, datatype=XSD.decimal)))
    g.add((node, EX.isValidated, Literal(is_validated, datatype=XSD.boolean)))

    # --- 6. SHACL VALIDATION ---
    conforms, _, results_text = validate(
        g,
        shacl_graph="schema/shapes.ttl",
        ont_graph="schema/ontology.ttl",
        inference='rdfs',
        advanced=True,
        allow_warnings=True
    )

    # --- 7. DETERMINISTIC PROMOTION ---
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

# --- 8. PRODUCTION TEST GATEWAY ---
if __name__ == "__main__":
    print("--- PADI BUREAU: NAIROBI NODE-01 STANDALONE AUDIT ---")

    # Example: Probabilistic / Should fail
    g1, c1, s1, r1 = audit_signal(
        name="Simulation_Lead",
        confidence=0.8,
        sources=["Source_1"],
        target_address="0xABCDEF1234567890",
        action_type="SWAP",
        signal_id="SIM-001",
        block_number=12345678,
        gas_price_gwei=50.0
    )
    print(f"Signal: Simulation_Lead | Status: {s1}")
    if not c1:
        print(f"Sentinel Report:\n{r1}\n")

    # Example: Deterministic / Should pass
    g2, c2, s2, r2 = audit_signal(
        name="Truth_Lead",
        confidence=1.0,
        sources=["Source_1", "Source_2", "Source_3"],
        target_address="0x1234567890ABCDEF",
        action_type="ARB",
        signal_id="TRUTH-001",
        block_number=12345679,
        gas_price_gwei=55.0
    )
    print(f"Signal: Truth_Lead | Status: {s2}")
