"""Endpoints de análise de modelagem de ameaças (placeholder para specs futuras)."""

from uuid import UUID

from fastapi import APIRouter, status

from src.api.dependencies import ApiKeyDep, SessionDep, StorageDep
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(
    prefix="/api/v1/threat-model",
    tags=["threat-model"],
    dependencies=[],  # API Key applied per-endpoint
)


@router.post(
    "/analyze",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Analyze architecture image",
    description="Upload and analyze an architecture diagram for threat modeling. (Placeholder - Spec 003)",
)
async def analyze_image(
    api_key: ApiKeyDep,
) -> dict:
    """Placeholder para endpoint de análise de imagem.

    Args:
        api_key: API Key validada.

    Returns:
        dict: ID do job para rastreamento da análise.
    """
    # Placeholder implementation
    return {
        "message": "Endpoint placeholder - Implement in Spec 003",
        "job_id": "placeholder",
        "status": "pending",
    }


@router.get(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Get analysis status",
    description="Get status of a threat modeling analysis job. (Placeholder - Spec 003)",
)
async def get_analysis_status(
    job_id: UUID,
    api_key: ApiKeyDep,
) -> dict:
    """Placeholder para obtenção de status do job.

    Args:
        job_id: UUID do job.
        api_key: API Key validada.

    Returns:
        dict: Informações de status do job.
    """
    return {
        "message": "Endpoint placeholder - Implement in Spec 003",
        "job_id": str(job_id),
        "status": "pending",
    }


@router.get(
    "/{job_id}/report",
    status_code=status.HTTP_200_OK,
    summary="Get analysis report",
    description="Get threat modeling report for completed analysis. (Placeholder - Spec 006)",
)
async def get_report(
    job_id: UUID,
    api_key: ApiKeyDep,
    format: str = "json",
) -> dict:
    """Placeholder para obtenção de relatório de análise.

    Args:
        job_id: UUID do job.
        api_key: API Key validada.
        format: Formato do relatório (json, md, html, pdf, csv).

    Returns:
        dict: Dados do relatório ou URL de download.
    """
    return {
        "message": "Endpoint placeholder - Implement in Spec 006",
        "job_id": str(job_id),
        "format": format,
    }
