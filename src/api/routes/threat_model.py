"""Endpoints de análise de modelagem de ameaças."""

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from src.api.dependencies import ApiKeyDep
from src.core.logging import get_logger
from src.core.security import validate_file_type, validate_file_size
from src.services.component_detector import (
    ComponentDetectionService,
    NoComponentsDetectedError,
)

logger = get_logger(__name__)
router = APIRouter(
    prefix="/api/v1/threat-model",
    tags=["threat-model"],
    dependencies=[],
)


@router.post(
    "/analyze",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Analyze architecture image",
    description="Upload and analyze an architecture diagram for threat modeling.",
)
async def analyze_image(
    api_key: ApiKeyDep,
    file: UploadFile = File(..., description="Architecture diagram image (PNG/JPG)"),
) -> dict:
    """Analisa imagem de arquitetura e retorna detecção de componentes.

    Args:
        api_key: API Key validada.
        file: Arquivo de imagem enviado.

    Returns:
        dict: ID do job e componentes detectados.

    Raises:
        HTTPException: Se arquivo inválido ou nenhum componente detectado.
    """
    # Validate file type and size
    content = await file.read()
    validate_file_size(content)
    validate_file_type(content)

    # Save file temporarily
    temp_path = Path(f"/tmp/uploads/{uuid4()}_{file.filename or 'upload.png'}")
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_bytes(content)

    logger.info(
        "Processing image upload",
        extra={
            "file_name": file.filename,
            "file_size": len(content),
            "content_type": file.content_type,
        },
    )

    try:
        # Run component detection
        detector = ComponentDetectionService()
        graph = await detector.detect(temp_path)

        job_id = uuid4()

        logger.info(
            "Detection completed",
            extra={
                "job_id": str(job_id),
                "components_found": len(graph.components),
                "using_stub": detector.is_using_stub,
            },
        )

        return {
            "job_id": str(job_id),
            "status": "completed",
            "components_found": len(graph.components),
            "graph": graph.model_dump(),
        }

    except NoComponentsDetectedError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.to_dict(),
        )

    except Exception as e:
        logger.error(
            "Detection failed",
            extra={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "DETECTION_FAILED", "message": str(e)},
        )

    finally:
        # Cleanup temp file
        if temp_path.exists():
            temp_path.unlink()


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
