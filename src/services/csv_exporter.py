"""Exportação de ameaças enriquecidas para formato CSV via pandas (RF-04)."""

import io
from typing import TYPE_CHECKING

from src.core.logging import get_logger
from src.domain.models import EnrichedThreat

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Colunas definidas pela Spec 006 RF-04
_COLUMNS = [
    "threat_id",
    "category",
    "category_name",
    "component_id",
    "component_type",
    "severity",
    "description",
    "cwe_id",
    "cwe_name",
    "cve_ids",
    "countermeasure_title",
    "countermeasure_description",
    "countermeasure_owasp_ref",
]

_STRIDE_NAMES: dict[str, str] = {
    "S": "Spoofing",
    "T": "Tampering",
    "R": "Repudiation",
    "I": "Information Disclosure",
    "D": "Denial of Service",
    "E": "Elevation of Privilege",
}


def _build_rows(threats: list[EnrichedThreat]) -> list[dict]:
    """Converte lista de EnrichedThreat em linhas flat para o DataFrame.

    Cada par (ameaça × contramedida) gera uma linha. Se a ameaça não tiver
    contramedidas, uma linha ainda é gerada com campos de contramedida em branco.

    Args:
        threats: Lista de ameaças enriquecidas.

    Returns:
        list[dict]: Linhas prontas para construção do DataFrame.
    """
    rows: list[dict] = []
    for threat in threats:
        base = {
            "threat_id": threat.id,
            "category": threat.category,
            "category_name": _STRIDE_NAMES.get(threat.category, threat.category),
            "component_id": threat.component_id,
            "component_type": threat.component_type,
            "severity": threat.severity.value,
            "description": threat.description,
            "cwe_id": threat.cwe_id or "",
            "cwe_name": threat.cwe_name or "",
            "cve_ids": "; ".join(threat.cve_ids) if threat.cve_ids else "",
        }
        if threat.countermeasures:
            for cm in threat.countermeasures:
                rows.append(
                    {
                        **base,
                        "countermeasure_title": cm.title,
                        "countermeasure_description": cm.description,
                        "countermeasure_owasp_ref": cm.owasp_ref or "",
                    }
                )
        else:
            rows.append(
                {
                    **base,
                    "countermeasure_title": "",
                    "countermeasure_description": "",
                    "countermeasure_owasp_ref": "",
                }
            )
    return rows


def export_to_csv_string(threats: list[EnrichedThreat]) -> str:
    """Gera CSV em memória como string UTF-8.

    Args:
        threats: Lista de ameaças enriquecidas.

    Returns:
        str: Conteúdo CSV com cabeçalho e linhas.
    """
    try:
        import pandas as pd  # lazy import — opcional em alguns ambientes
    except ImportError as exc:
        raise ImportError(
            "pandas é necessário para exportação CSV. "
            "Instale com: pip install pandas"
        ) from exc

    rows = _build_rows(threats)

    if not rows:
        df = pd.DataFrame(columns=_COLUMNS)
    else:
        df = pd.DataFrame(rows, columns=_COLUMNS)

    buffer = io.StringIO()
    df.to_csv(buffer, index=False, encoding="utf-8")
    csv_content = buffer.getvalue()
    logger.debug(f"CSV gerado: {len(rows)} linhas, {len(csv_content)} bytes")
    return csv_content


def export_to_csv_bytes(threats: list[EnrichedThreat]) -> bytes:
    """Gera CSV como bytes UTF-8-BOM (compatível com Excel).

    Args:
        threats: Lista de ameaças enriquecidas.

    Returns:
        bytes: Conteúdo CSV codificado em UTF-8 com BOM.
    """
    try:
        import pandas as pd
    except ImportError as exc:
        raise ImportError(
            "pandas é necessário para exportação CSV. "
            "Instale com: pip install pandas"
        ) from exc

    rows = _build_rows(threats)

    if not rows:
        df = pd.DataFrame(columns=_COLUMNS)
    else:
        df = pd.DataFrame(rows, columns=_COLUMNS)

    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding="utf-8-sig")  # BOM para Excel
    return buffer.getvalue()
