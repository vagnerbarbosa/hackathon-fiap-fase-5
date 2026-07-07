"""Mock Threats for Spec 005 and 006 testing."""

from uuid import uuid4

from domain.models import Severity, Threat

fake_threats = [
    Threat(
        id=str(uuid4()),
        category="T",
        component_id="comp-db-1",
        component_type="database",
        description="Possibilidade de alteração não autorizada dos dados em repouso.",
        severity=Severity.HIGH,
        affected_data_flows=[],
    ),
    Threat(
        id=str(uuid4()),
        category="I",
        component_id="comp-db-1",
        component_type="database",
        description="Exfiltração de dados sensíveis sem criptografia.",
        severity=Severity.CRITICAL,
        affected_data_flows=[],
    ),
    Threat(
        id=str(uuid4()),
        category="D",
        component_id="comp-api-1",
        component_type="api",
        description="Negação de serviço por falta de rate limiting.",
        severity=Severity.MEDIUM,
        affected_data_flows=["flow-1"],
    ),
]

if __name__ == "__main__":
    print(f"Created {len(fake_threats)} mock threats")
    for threat in fake_threats:
        print(f"  - [{threat.category}] {threat.severity.value}: {threat.description[:50]}...")
