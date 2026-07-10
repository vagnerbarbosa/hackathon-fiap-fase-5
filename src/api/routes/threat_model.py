"""Threat model analysis endpoints."""

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import ApiKeyDep, get_db, get_storage
from src.core.logging import get_logger
from src.core.security import validate_file_type, validate_file_size
from src.domain.models import Job, JobStatus
from src.infrastructure.storage import LocalFileStorage
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
    """Analyze architecture image and return component detection.

    Args:
        api_key: Validated API Key.
        file: Uploaded image file.

    Returns:
        dict: Job ID and detected components.

    Raises:
        HTTPException: If file invalid or no components detected.
    """
    from fastapi import Depends
    from src.api.dependencies import get_db, get_storage

    # Get dependencies
    db = Depends(get_db)
    storage = Depends(get_storage)

    # Validate file type and size
    content = await file.read()
    validate_file_size(content)
    validate_file_type(content)

    # Save file to storage
    safe_filename = storage.sanitize_filename(file.filename or "upload.png")
    image_path = await storage.save(content, safe_filename)

    logger.info(
        "Processing image upload",
        extra={
            "filename": safe_filename,
            "size": len(content),
            "content_type": file.content_type,
        },
    )

    # Create job in database
    job = Job(
        id=uuid4(),
        status=JobStatus.PROCESSING,
        input_image_path=str(image_path),
        output_report_path=None,
    )
    db.add(job)
    await db.commit()

    try:
        # Run component detection
        detector = ComponentDetectionService()
        graph = await detector.detect(image_path)

        # Update job status
        job.status = JobStatus.COMPLETED
        await db.commit()

        logger.info(
            "Detection completed",
            extra={
                "job_id": str(job.id),
                "components_found": len(graph.components),
                "using_stub": detector.is_using_stub,
            },
        )

        return {
            "job_id": str(job.id),
            "status": "completed",
            "components_found": len(graph.components),
            "graph": graph.model_dump(),
        }

    except NoComponentsDetectedError as e:
        job.status = JobStatus.FAILED
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.to_dict(),
        )

    except Exception as e:
        job.status = JobStatus.FAILED
        await db.commit()
        logger.error(
            "Detection failed",
            extra={
                "job_id": str(job.id),
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "DETECTION_FAILED", "message": str(e)},
        )


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
    """Placeholder for getting job status.

    Args:
        job_id: Job UUID.
        api_key: Validated API Key.

    Returns:
        dict: Job status information.
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
    """Placeholder for getting analysis report.

    Args:
        job_id: Job UUID.
        api_key: Validated API Key.
        format: Report format (json, md, html, pdf, csv).

    Returns:
        dict: Report data or download URL.
    """
    return {
        "message": "Endpoint placeholder - Implement in Spec 006",
        "job_id": str(job_id),
        "format": format,
    }
