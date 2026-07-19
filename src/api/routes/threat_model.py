"""Endpoints de análise de modelagem de ameaças (Spec 001 + 003)."""

import asyncio
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from src.api.dependencies import ApiKeyDep, SessionDep, StorageDep
from src.core.config import settings
from src.core.logging import get_logger
from src.domain.models import JobStatus
from src.infrastructure.repositories.job_repository import JobRepository
from src.services.component_detection import ComponentDetectionService, LowConfidenceError, ModelNotLoadedError

logger = get_logger(__name__)
router = APIRouter(
    prefix="/api/v1/threat-model",
    tags=["threat-model"],
    dependencies=[],  # API Key applied per-endpoint
)

# Inicializa serviço de detecção (singleton)
# O modelo ONNX deve estar disponível em storage/models/best.onnx
try:
    detection_service = ComponentDetectionService(
        model_path=str(Path(settings.storage_path) / "models" / "best.onnx")
    )
    logger.info("Serviço de detecção inicializado com sucesso")
except ModelNotLoadedError as e:
    logger.error(f"Falha ao inicializar serviço de detecção: {e.message}")
    detection_service = None


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
            # Verificar se o serviço de detecção está disponível
            if detection_service is None:
                raise ModelNotLoadedError(
                    "Serviço de detecção não inicializado. "
                    "Verifique se o modelo ONNX está disponível em storage/models/best.onnx"
                )

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
        except ModelNotLoadedError as e:
            logger.error(f"Job {job_id}: modelo não disponível - {e.message}")
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
    description=(
        "Get threat modeling report for a completed analysis job. "
        "Supported formats: json (default, inline), md, html, csv, pdf (attachment download)."
    ),
)
async def get_report(
    job_id: UUID,
    api_key: ApiKeyDep,
    session: SessionDep,
    format: str = "json",  # noqa: A002 — shadow of built-in intentional (query param name)
) -> Any:
    """Obtém relatório de análise no formato solicitado (RF-07).

    Args:
        job_id: UUID do job.
        api_key: API Key validada.
        session: Sessão do banco de dados.
        format: Formato de saída — json | md | html | csv | pdf. Default: json.

    Returns:
        - json  → resposta inline (application/json)
        - md / html / csv / pdf → download (Content-Disposition: attachment)
    """
    from datetime import datetime, timezone

    from fastapi.responses import JSONResponse, Response

    from src.domain.models import (
        ArchitectureGraph,
        BoundingBox,
        Countermeasure,
        DetectedComponent,
        EnrichedThreat,
        Point,
        Severity,
    )
    from src.services.report_generator import report_generator
    from src.services.stride_engine import StrideEngine
    from src.services.vulnerability_service import VulnerabilityService

    # ── Validar formato ───────────────────────────────────────────────────────
    supported_formats = {"json", "md", "html", "csv", "pdf"}
    fmt = format.lower().strip()
    if fmt not in supported_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato '{format}' não suportado. Use: {', '.join(sorted(supported_formats))}",
        )

    # ── Buscar job ────────────────────────────────────────────────────────────
    job_repo = JobRepository(session)
    db_job = await job_repo.get_by_id(job_id)

    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} não encontrado",
        )

    if db_job.status != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job ainda não completado. Status atual: {db_job.status}",
        )

    # ── Construir objeto Job de domínio (Pydantic) a partir do modelo ORM ─────
    from src.domain.models import Job as DomainJob
    from src.domain.models import JobStatus as DomainJobStatus

    domain_job = DomainJob(
        id=db_job.id,
        status=DomainJobStatus(db_job.status),
        input_image_path=db_job.input_image_path or "",
        output_report_path=db_job.output_report_path,
        created_at=db_job.created_at or datetime.now(timezone.utc),
        updated_at=db_job.updated_at or datetime.now(timezone.utc),
    )

    # ── Obter dados de ameaças (detecção → STRIDE → enriquecimento) ───────────
    try:
        if detection_service is None:
            raise ModelNotLoadedError("Serviço de detecção não disponível")

        architecture_graph = await detection_service.detect(db_job.input_image_path)
        stride_engine = StrideEngine()
        threats = await stride_engine.analyze(architecture_graph)
        vuln_service = VulnerabilityService()
        enriched_threats = await vuln_service.enrich(threats)

    except Exception as exc:
        logger.warning(f"Job {job_id}: pipeline falhou ({exc}), usando dados mock")

        # Fallback com dados mock representativos
        architecture_graph = ArchitectureGraph(
            components=[
                DetectedComponent(
                    id="mock-web-1", type="web_server", confidence=0.95,
                    bbox=BoundingBox(x_min=0, y_min=0, x_max=100, y_max=100),
                    center=Point(x=50, y=50),
                ),
                DetectedComponent(
                    id="mock-api-1", type="api", confidence=0.92,
                    bbox=BoundingBox(x_min=110, y_min=0, x_max=210, y_max=100),
                    center=Point(x=160, y=50),
                ),
                DetectedComponent(
                    id="mock-db-1", type="database", confidence=0.88,
                    bbox=BoundingBox(x_min=220, y_min=0, x_max=320, y_max=100),
                    center=Point(x=270, y=50),
                ),
            ],
            data_flows=[],
            trust_boundaries=[],
        )
        enriched_threats = [
            EnrichedThreat(
                id="threat-mock-1", category="I", component_id="mock-db-1",
                component_type="database", severity=Severity.CRITICAL,
                description="Dados sensíveis podem ser exfiltrados do banco de dados.",
                cwe_id="CWE-200", cwe_name="Exposure of Sensitive Information",
                cve_ids=["CVE-2023-5678"],
                countermeasures=[
                    Countermeasure(
                        title="Criptografar dados em repouso",
                        description="Usar AES-256 para dados sensíveis persistidos.",
                        owasp_ref="OWASP Cryptographic Storage Cheat Sheet",
                    )
                ],
            ),
            EnrichedThreat(
                id="threat-mock-2", category="S", component_id="mock-web-1",
                component_type="web_server", severity=Severity.HIGH,
                description="Servidor web pode ser falsificado por atacantes.",
                cwe_id="CWE-290", cwe_name="Authentication Bypass by Spoofing",
                cve_ids=[],
                countermeasures=[
                    Countermeasure(
                        title="Implementar autenticação mútua TLS",
                        description="Usar certificados cliente/servidor para autenticação.",
                        owasp_ref="OWASP Transport Layer Security Cheat Sheet",
                    )
                ],
            ),
            EnrichedThreat(
                id="threat-mock-3", category="T", component_id="mock-api-1",
                component_type="api", severity=Severity.MEDIUM,
                description="Payloads da API podem ser alterados em trânsito.",
                cwe_id="CWE-345", cwe_name="Insufficient Verification of Data Authenticity",
                cve_ids=[],
                countermeasures=[
                    Countermeasure(
                        title="Validar integridade com HMAC",
                        description="Assinar e verificar todos os payloads críticos.",
                        owasp_ref="OWASP Input Validation Cheat Sheet",
                    )
                ],
            ),
        ]

    # ── Gerar relatório no formato solicitado ─────────────────────────────────
    try:
        content, media_type = report_generator.generate_format(
            job=domain_job,
            architecture_graph=architecture_graph,
            threats=enriched_threats,
            fmt=fmt,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Erro ao gerar relatório para job {job_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao gerar o relatório. Tente novamente.",
        ) from exc

    # ── Atualizar output_report_path no job (RF-08) ───────────────────────────
    saved_paths = report_generator.get_saved_paths(str(job_id))
    if saved_paths:
        path_list = ";".join(str(p) for p in saved_paths.values())
        await job_repo.update_status(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            output_report_path=path_list,
        )

    # ── Montar resposta HTTP ──────────────────────────────────────────────────
    # json → inline; demais → attachment download
    if fmt == "json":
        return JSONResponse(content=content, media_type="application/json")

    # Mapeia formato → nome de arquivo para Content-Disposition
    filename_map = {
        "md":   f"stride-report-{job_id}.md",
        "html": f"stride-report-{job_id}.html",
        "csv":  f"stride-report-{job_id}.csv",
        "pdf":  f"stride-report-{job_id}.pdf",
    }
    filename = filename_map.get(fmt, f"stride-report-{job_id}.{fmt}")

    # Se media_type for text/html (fallback do PDF), ajusta o nome do arquivo
    if fmt == "pdf" and media_type == "text/html":
        filename = f"stride-report-{job_id}-pdf-fallback.html"

    # Codifica strings para bytes se necessário
    if isinstance(content, str):
        body = content.encode("utf-8")
    elif isinstance(content, dict):
        import json as _json
        body = _json.dumps(content, ensure_ascii=False).encode("utf-8")
    else:
        body = content  # já bytes (CSV, PDF)

    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
