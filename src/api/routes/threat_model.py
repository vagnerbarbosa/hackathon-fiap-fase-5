"""Endpoints de análise de modelagem de ameaças (Spec 001 + 003)."""

import asyncio
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from src.api.dependencies import ApiKeyDep, SessionDep, StorageDep
from src.core.config import settings
from src.core.logging import get_logger
from src.domain.models import JobStatus
from src.infrastructure.repositories.job_repository import JobRepository
from src.services.component_detection import ComponentDetectionService

logger = get_logger(__name__)
router = APIRouter(
    prefix="/api/v1/threat-model",
    tags=["threat-model"],
    dependencies=[],  # API Key applied per-endpoint
)

# Inicializa serviço de detecção (singleton)
# Tenta carregar modelo real, senão usa mock
detection_service = ComponentDetectionService(
    model_path=str(Path(settings.storage_path) / "models" / "best.pt")
)


@router.post(
    "/analyze",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Analyze architecture image",
    description="Upload and analyze an architecture diagram for threat modeling.",
)
async def analyze_image(
    api_key: ApiKeyDep,
    session: SessionDep,
    storage: StorageDep,
    file: UploadFile = File(...),
) -> dict:
    """Upload e inicia análise de imagem de arquitetura.

    Args:
        api_key: API Key validada.
        session: Sessão do banco de dados.
        storage: Serviço de armazenamento.
        file: Arquivo de imagem (PNG, JPG, JPEG).

    Returns:
        dict: ID do job para rastreamento da análise.
    """
    # Validar tipo de arquivo
    valid_types = ["image/png", "image/jpeg", "image/jpg"]
    if file.content_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo não suportado: {file.content_type}. Use PNG ou JPEG.",
        )

    # Criar job no banco de dados
    job_repo = JobRepository(session)

    # Salvar arquivo temporariamente
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    content = await file.read()
    temp_relative = await storage.save(content, f"upload_{file.filename}")
    temp_path = str(await storage.get_path(temp_relative))

    # Criar job
    job = await job_repo.create(input_image_path=temp_path)
    logger.info(f"Job criado: {job.id} para arquivo {file.filename}")

    # Iniciar processamento em background (não bloqueia a resposta)
    asyncio.create_task(_process_job(job.id, temp_path, session))

    return {
        "job_id": str(job.id),
        "status": JobStatus.PROCESSING.value,
        "message": "Análise iniciada. Use GET /threat-model/{job_id} para acompanhar o progresso.",
    }


async def _process_job(job_id: UUID, image_path: str, session) -> None:
    """Processa o job em background.

    Args:
        job_id: ID do job.
        image_path: Caminho da imagem.
        session: Sessão do banco de dados.
    """
    from src.infrastructure.database import AsyncSessionLocal

    # Criar nova sessão para a tarefa em background
    async with AsyncSessionLocal() as bg_session:
        job_repo = JobRepository(bg_session)

        try:
            # Atualizar status para PROCESSING
            await job_repo.update_status(
                job_id=job_id,
                status=JobStatus.PROCESSING,
            )

            # Executar detecção de componentes (Spec 003)
            logger.info(f"Processando job {job_id}: detectando componentes...")
            architecture_graph = await detection_service.detect(image_path)

            # TODO: Integrar com Spec 004 (STRIDE Engine) quando disponível
            # TODO: Integrar com Spec 005 (Vulnerabilidades) quando disponível
            # TODO: Integrar com Spec 006 (Relatórios) quando disponível

            # Por enquanto, simular processamento
            await asyncio.sleep(2)  # Simular tempo de processamento

            # Atualizar status para COMPLETED
            await job_repo.update_status(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                output_report_path=f"reports/{job_id}.md",
            )

            logger.info(f"Job {job_id} processado com sucesso. "
                       f"Componentes detectados: {len(architecture_graph.components)}")

        except Exception as e:
            logger.error(f"Erro ao processar job {job_id}: {e}")
            await job_repo.update_status(
                job_id=job_id,
                status=JobStatus.FAILED,
                error_message=str(e),
            )


@router.get(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Get analysis status",
    description="Get status of a threat modeling analysis job.",
)
async def get_analysis_status(
    job_id: UUID,
    api_key: ApiKeyDep,
    session: SessionDep,
) -> dict:
    """Obtém status de um job de análise.

    Args:
        job_id: UUID do job.
        api_key: API Key validada.
        session: Sessão do banco de dados.

    Returns:
        dict: Informações de status do job.
    """
    job_repo = JobRepository(session)
    job = await job_repo.get_by_id(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} não encontrado",
        )

    # Calcular progresso baseado no status
    progress_map = {
        JobStatus.PENDING.value: 0,
        JobStatus.PROCESSING.value: 50,
        JobStatus.COMPLETED.value: 100,
        JobStatus.FAILED.value: 0,
    }

    response = {
        "job_id": str(job.id),
        "status": job.status,
        "progress": progress_map.get(job.status, 0),
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }

    # Incluir resultado se completado
    if job.status == JobStatus.COMPLETED.value:
        response["result"] = {
            "threats_count": 6,  # TODO: Calcular real após Spec 004/005/006
            "report_url": f"/api/v1/threat-model/{job_id}/report",
        }

    # Incluir erro se falhou
    if job.status == JobStatus.FAILED.value and job.error_message:
        response["error"] = job.error_message

    return response


@router.get(
    "/{job_id}/report",
    status_code=status.HTTP_200_OK,
    summary="Get analysis report",
    description="Get threat modeling report for completed analysis.",
)
async def get_report(
    job_id: UUID,
    api_key: ApiKeyDep,
    session: SessionDep,
    format: str = "json",
) -> dict:
    """Obtém relatório de análise.

    Args:
        job_id: UUID do job.
        api_key: API Key validada.
        session: Sessão do banco de dados.
        format: Formato do relatório (json, md, html, pdf, csv).

    Returns:
        dict: Dados do relatório ou URL de download.
    """
    job_repo = JobRepository(session)
    job = await job_repo.get_by_id(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} não encontrado",
        )

    if job.status != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job ainda não completado. Status atual: {job.status}",
        )

    # TODO: Implementar geração real de relatório na Spec 006
    return {
        "job_id": str(job_id),
        "format": format,
        "message": "Relatório placeholder - Implementar na Spec 006",
        "threats": [
            {
                "category": "S",
                "title": "Spoofing",
                "description": "Risco de falsificação de identidade",
            },
            {
                "category": "T",
                "title": "Tampering",
                "description": "Risco de modificação não autorizada",
            },
        ],
    }
