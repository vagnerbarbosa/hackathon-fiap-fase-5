"""Regras de severidade e ordenacao para analise STRIDE."""

from domain.models import Severity


SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}

STRIDE_CATEGORY_NAMES = {
    "S": "Spoofing",
    "T": "Tampering",
    "R": "Repudiation",
    "I": "Information Disclosure",
    "D": "Denial of Service",
    "E": "Elevation of Privilege",
}


def calculate_severity(
    component_type: str,
    category: str,
    *,
    crosses_trust_boundary: bool = False,
) -> Severity:
    """Retorna a severidade deterministica de uma ameaca STRIDE."""
    normalized_type = component_type.lower()

    if normalized_type in {"database", "storage"} and category in {"I", "T"}:
        return Severity.CRITICAL

    if crosses_trust_boundary:
        return Severity.HIGH

    if normalized_type in {"api", "container"} and category == "E":
        return Severity.HIGH

    if normalized_type == "web_server" and category == "D":
        return Severity.MEDIUM

    if normalized_type == "queue" and category == "S":
        return Severity.MEDIUM

    if normalized_type == "api" and category in {"S", "T", "I", "D"}:
        return Severity.MEDIUM

    return Severity.LOW


def severity_sort_rank(severity: Severity) -> int:
    """Mapeia severidade para ordenacao ascendente."""
    return SEVERITY_ORDER[severity]


def category_name(category: str) -> str:
    """Retorna o nome canonico de uma categoria STRIDE."""
    return STRIDE_CATEGORY_NAMES[category]
