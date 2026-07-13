"""Mock EnrichedThreats for Spec 006 testing."""

from uuid import uuid4

from domain.models import Countermeasure, EnrichedThreat, Severity

fake_enriched = [
    EnrichedThreat(
        id=str(uuid4()),
        category="T",
        category_name="Tampering",
        component_id="comp-db-1",
        component_type="database",
        description="Possibilidade de alteração não autorizada dos dados em repouso.",
        justification="Bancos armazenam dados persistentes que exigem integridade.",
        severity=Severity.HIGH,
        cwe_id="CWE-522",
        cwe_name="Insufficiently Protected Credentials",
        cve_ids=["CVE-2023-1234"],
        countermeasures=[
            Countermeasure(
                title="TLS 1.3",
                description="Criptografia em trânsito.",
                owasp_ref="Cheat Sheet: Transport Layer Protection",
            ),
            Countermeasure(
                title="AES-256",
                description="Criptografia em repouso.",
                owasp_ref="Cheat Sheet: Cryptographic Storage",
            ),
        ],
    ),
]

if __name__ == "__main__":
    print(f"Created {len(fake_enriched)} mock enriched threats")
    for threat in fake_enriched:
        print(f"  - [{threat.category}] CWE: {threat.cwe_id}")
        print(f"    Countermeasures: {len(threat.countermeasures)}")
