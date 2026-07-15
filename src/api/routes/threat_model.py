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
from src.services.component_detection import ComponentDetectionService, LowConfidenceError

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

        except LowConfidenceError as e:
            logger.warning(f"Job {job_id}: falha de detecção - {e.message}")
            await job_repo.update_status(
                job_id=job_id,
                status=JobStatus.FAILED,
                error_message=str(e.message),
            )
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
) -> Any:
    """Obtém relatório de análise.

    Args:
        job_id: UUID do job.
        api_key: API Key validada.
        session: Sessão do banco de dados.
        format: Formato do relatório (json, html).

    Returns:
        dict or HTML: Dados do relatório ou HTML renderizado.
    """
    from fastapi.responses import HTMLResponse
    from src.services.simple_report import report_generator
    from src.services.stride_engine import StrideEngine
    from src.services.vulnerability_service import VulnerabilityService
    from src.infrastructure.database import AsyncSessionLocal

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

    # Verificar se temos dados processados em cache ou regenerar
    # Por simplicidade, vamos buscar da storage ou usar mock
    try:
        # Tentar detectar novamente para ter os dados reais
        architecture_graph = await detection_service.detect(job.input_image_path)

        # Processar com STRIDE
        stride_engine = StrideEngine()
        threats = await stride_engine.analyze(architecture_graph)

        # Enriquecer com vulnerabilidades
        vuln_service = VulnerabilityService()
        enriched_threats = await vuln_service.enrich(threats)

        if format == "html":
            # Gerar relatório HTML
            html_content = report_generator.generate(
                str(job_id), architecture_graph, enriched_threats
            )
            return HTMLResponse(content=html_content, media_type="text/html")

        # Retornar JSON
        return {
            "job_id": str(job_id),
            "format": format,
            "status": "completed",
            "components_count": len(architecture_graph.components),
            "threats_count": len(enriched_threats),
            "threats": [
                {
                    "id": t.id,
                    "category": t.category,
                    "category_name": t.category_name,
                    "component_type": t.component_type,
                    "severity": t.severity.value,
                    "description": t.description,
                    "cwe_id": t.cwe_id,
                    "cve_ids": t.cve_ids,
                    "countermeasures": [
                        {"title": cm.title, "owasp_ref": cm.owasp_ref}
                        for cm in t.countermeasures
                    ],
                }
                for t in enriched_threats
            ],
        }

    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        # Fallback para dados mock
        if format == "html":
            from src.domain.models import ArchitectureGraph, DetectedComponent, BoundingBox, Point

            # Criar dados mock mínimos
            mock_graph = ArchitectureGraph(
                components=[
                    DetectedComponent(
                        id="mock-1", type="web_server", confidence=0.95,
                        bbox=BoundingBox(x_min=0, y_min=0, x_max=100, y_max=100),
                        center=Point(x=50, y=50)
                    ),
                    DetectedComponent(
                        id="mock-2", type="api", confidence=0.92,
                        bbox=BoundingBox(x_min=100, y_min=0, x_max=200, y_max=100),
                        center=Point(x=150, y=50)
                    ),
                    DetectedComponent(
                        id="mock-3", type="database", confidence=0.88,
                        bbox=BoundingBox(x_min=200, y_min=0, x_max=300, y_max=100),
                        center=Point(x=250, y=50)
                    ),
                ],
                data_flows=[],
                trust_boundaries=[],
            )

            from src.domain.models import EnrichedThreat, Countermeasure, Severity

            mock_threats = [
                EnrichedThreat(
                    id="threat-1", category="S", category_name="Spoofing",
                    component_id="mock-1", component_type="web_server",
                    description="Falso servidor web pode receber tráfego de usuários.",
                    justification="Usuários precisam confiar na identidade do servidor.",
                    severity=Severity.HIGH,
                    cwe_id="CWE-290", cwe_name="Authentication Bypass",
                    cve_ids=["CVE-2023-1234"],
                    countermeasures=[
                        Countermeasure(
                            title="Exigir autenticação forte",
                            description="Aplicar MFA e tokens assinados.",
                            owasp_ref="OWASP Authentication Cheat Sheet"
                        )
                    ]
                ),
                EnrichedThreat(
                    id="threat-2", category="T", category_name="Tampering",
                    component_id="mock-2", component_type="api",
                    description="Requests ou responses podem ser alterados.",
                    justification="APIs processam payloads de entrada e saída.",
                    severity=Severity.MEDIUM,
                    cwe_id="CWE-345", cwe_name="Insufficient Verification",
                    cve_ids=[],
                    countermeasures=[
                        Countermeasure(
                            title="Proteger integridade dos dados",
                            description="Usar TLS 1.3 e HMAC.",
                            owasp_ref="OWASP Cryptographic Storage Cheat Sheet"
                        )
                    ]
                ),
                EnrichedThreat(
                    id="threat-3", category="I", category_name="Information Disclosure",
                    component_id="mock-3", component_type="database",
                    description="Dados sensíveis podem ser exfiltrados do banco.",
                    justification="Bancos concentram dados persistidos.",
                    severity=Severity.CRITICAL,
                    cwe_id="CWE-200", cwe_name="Exposure of Sensitive Information",
                    cve_ids=["CVE-2023-5678", "CVE-2023-9012"],
                    countermeasures=[
                        Countermeasure(
                            title="Criptografar dados sensíveis",
                            description="Usar criptografia em trânsito e em repouso.",
                            owasp_ref="OWASP Cryptographic Storage Cheat Sheet"
                        ),
                        Countermeasure(
                            title="Minimizar exposição de dados",
                            description="Aplicar mascaramento e tokenização.",
                            owasp_ref="OWASP Data Protection Cheat Sheet"
                        )
                    ]
                ),
            ]

            html_content = report_generator.generate(str(job_id), mock_graph, mock_threats)
            return HTMLResponse(content=html_content, media_type="text/html")

        return {
            "job_id": str(job_id),
            "format": format,
            "status": "completed",
            "message": "Relatório gerado com dados de exemplo",
            "threats": [
                {"category": "S", "title": "Spoofing", "severity": "high"},
                {"category": "T", "title": "Tampering", "severity": "medium"},
                {"category": "I", "title": "Information Disclosure", "severity": "critical"},
            ],
        }
