"""Testes para rotas de threat model da API."""

import asyncio
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import app
from src.api.routes.threat_model import _process_job
from src.domain.models import (
    ArchitectureGraph,
    BoundingBox,
    Countermeasure,
    DataFlow,
    DetectedComponent,
    EnrichedThreat,
    JobStatus,
    Point,
    Severity,
    Threat,
)
from src.infrastructure.database import AsyncSessionLocal
from src.infrastructure.repositories.job_repository import JobRepository
from src.services.report_generator import GeneratedReport


@pytest_asyncio.fixture
async def anonymous_client() -> AsyncClient:
    """Cliente HTTP sem API key."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def sample_graph() -> ArchitectureGraph:
    """Grafo de arquitetura mock para testes."""
    return ArchitectureGraph(
        components=[
            DetectedComponent(
                id="comp-web-1",
                type="web_server",
                confidence=0.95,
                bbox=BoundingBox(x_min=0, y_min=0, x_max=100, y_max=100),
                center=Point(x=50, y=50),
            ),
            DetectedComponent(
                id="comp-api-1",
                type="api",
                confidence=0.92,
                bbox=BoundingBox(x_min=110, y_min=0, x_max=210, y_max=100),
                center=Point(x=160, y=50),
            ),
        ],
        data_flows=[
            DataFlow(
                source_id="comp-web-1",
                target_id="comp-api-1",
                direction="unidirectional",
                inferred=True,
            ),
        ],
        trust_boundaries=[["comp-web-1"], ["comp-api-1"]],
    )


@pytest.fixture
def sample_threats() -> list[Threat]:
    """Ameaças STRIDE mock para testes."""
    return [
        Threat(
            id="threat-s-1",
            category="S",
            component_id="comp-web-1",
            component_type="web_server",
            severity=Severity.HIGH,
            description="Spoofing do servidor web.",
        ),
        Threat(
            id="threat-t-1",
            category="T",
            component_id="comp-api-1",
            component_type="api",
            severity=Severity.MEDIUM,
            description="Tampering na API.",
        ),
    ]


@pytest.fixture
def sample_enriched_threats() -> list[EnrichedThreat]:
    """Ameaças enriquecidas mock para testes."""
    return [
        EnrichedThreat(
            id="threat-001",
            category="S",
            component_id="comp-web-1",
            component_type="web_server",
            severity=Severity.HIGH,
            description="Spoofing do servidor web.",
            cwe_id="CWE-290",
            cwe_name="Authentication Bypass by Spoofing",
            cve_ids=[],
            countermeasures=[
                Countermeasure(
                    title="TLS mútuo",
                    description="Usar certificados cliente/servidor.",
                    owasp_ref="OWASP TLS Cheat Sheet",
                )
            ],
        ),
    ]


@pytest.fixture
def mock_detection_service(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock do serviço de detecção para testes."""
    mock_service = MagicMock()
    mock_service.is_using_stub = False
    mock_service.detect = AsyncMock()
    monkeypatch.setattr(
        "src.api.routes.threat_model.detection_service",
        mock_service,
    )
    return mock_service


@pytest.fixture
def mock_report_generator(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock do gerador de relatórios para testes."""
    mock_gen = MagicMock()
    mock_gen.generate_format = MagicMock(
        return_value=({"job_id": str(uuid4()), "threats": []}, "application/json")
    )
    mock_gen.get_saved_paths = MagicMock(return_value={})
    monkeypatch.setattr(
        "src.api.routes.threat_model.report_generator",
        mock_gen,
    )
    return mock_gen


@pytest.fixture
def patched_storage_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redireciona storage_path para tmp_path durante o teste."""
    monkeypatch.setattr(
        "src.api.routes.threat_model.settings.storage_path",
        str(tmp_path),
    )
    return tmp_path


def _make_generated_report(
    job_id: str,
    base_dir: Path,
    threats: list[dict] | None = None,
) -> GeneratedReport:
    """Cria um GeneratedReport com arquivos de relatório em base_dir."""
    report_dir = base_dir / "reports" / job_id
    report_dir.mkdir(parents=True, exist_ok=True)

    threats_data = threats if threats is not None else []
    json_data = {
        "job_id": job_id,
        "threats": threats_data,
        "summary": {"total_threats": len(threats_data)},
    }
    json_path = report_dir / "report.json"
    json_path.write_text(json.dumps(json_data), encoding="utf-8")

    md_path = report_dir / "report.md"
    md_path.write_text(f"# Report {job_id}", encoding="utf-8")

    html_path = report_dir / "report.html"
    html_path.write_text(f"<html>{job_id}</html>", encoding="utf-8")

    csv_path = report_dir / "report.csv"
    csv_path.write_bytes(b"id,category\n")

    pdf_path = report_dir / "report.pdf"
    pdf_path.write_bytes(b"%PDF")

    return GeneratedReport(
        job_id=job_id,
        saved_paths={
            "json": json_path,
            "md": md_path,
            "html": html_path,
            "csv": csv_path,
            "pdf": pdf_path,
        },
        json_data=json_data,
    )


@pytest.fixture
def mock_pipeline_services(
    monkeypatch: pytest.MonkeyPatch,
    sample_graph: ArchitectureGraph,
    sample_enriched_threats: list[EnrichedThreat],
) -> dict[str, MagicMock]:
    """Mocka os serviços do pipeline end-to-end (detecção, STRIDE, vuln)."""
    detection_service = MagicMock()
    detection_service.detect = AsyncMock(return_value=sample_graph)
    monkeypatch.setattr(
        "src.api.routes.threat_model.detection_service",
        detection_service,
    )

    stride_instance = MagicMock()
    stride_instance.analyze = AsyncMock(return_value=[])
    stride_cls = MagicMock(return_value=stride_instance)
    monkeypatch.setattr(
        "src.api.routes.threat_model.StrideEngine",
        stride_cls,
    )

    vuln_instance = MagicMock()
    vuln_instance.enrich = AsyncMock(return_value=sample_enriched_threats)
    vuln_cls = MagicMock(return_value=vuln_instance)
    monkeypatch.setattr(
        "src.api.routes.threat_model.VulnerabilityService",
        vuln_cls,
    )

    return {
        "detection_service": detection_service,
        "stride_cls": stride_cls,
        "stride_instance": stride_instance,
        "vuln_cls": vuln_cls,
        "vuln_instance": vuln_instance,
    }


class TestThreatModelAuth:
    """Testes de autenticação nos endpoints de threat model."""

    async def test_analyze_requires_api_key(self, anonymous_client: AsyncClient):
        """Deve retornar 401 sem API key."""
        response = await anonymous_client.post("/api/v1/threat-model/analyze")
        assert response.status_code == 401

    async def test_get_status_requires_api_key(self, anonymous_client: AsyncClient):
        """Deve retornar 401 sem API key."""
        response = await anonymous_client.get(f"/api/v1/threat-model/{uuid4()}")
        assert response.status_code == 401

    async def test_get_report_requires_api_key(self, anonymous_client: AsyncClient):
        """Deve retornar 401 sem API key."""
        response = await anonymous_client.get(f"/api/v1/threat-model/{uuid4()}/report")
        assert response.status_code == 401


class TestThreatModelResponses:
    """Testes de respostas dos endpoints de threat model."""

    async def test_status_returns_json(self, async_client: AsyncClient):
        """Endpoint de status deve retornar JSON."""
        response = await async_client.get(f"/api/v1/threat-model/{uuid4()}")
        assert response.headers.get("content-type") == "application/json"

    async def test_report_returns_json(self, async_client: AsyncClient):
        """Endpoint de relatório deve retornar JSON."""
        response = await async_client.get(f"/api/v1/threat-model/{uuid4()}/report")
        assert response.headers.get("content-type") == "application/json"

    async def test_analyze_rejects_text(self, async_client: AsyncClient):
        """Deve rejeitar arquivos de texto."""
        files = {"file": ("test.txt", BytesIO(b"content"), "text/plain")}
        response = await async_client.post(
            "/api/v1/threat-model/analyze",
            files=files,
        )
        assert response.status_code == 400

    async def test_analyze_requires_file(self, async_client: AsyncClient):
        """Deve requerer arquivo no upload."""
        response = await async_client.post("/api/v1/threat-model/analyze")
        assert response.status_code == 422

    async def test_analyze_rejects_unsupported_image_type(self, async_client: AsyncClient):
        """Deve rejeitar tipos de imagem não suportados."""
        files = {"file": ("test.gif", BytesIO(b"GIF89a"), "image/gif")}
        response = await async_client.post(
            "/api/v1/threat-model/analyze",
            files=files,
        )
        assert response.status_code == 400


class TestThreatModelAnalyze:
    """Testes de análise de imagem."""

    async def test_analyze_accepts_png(
        self,
        async_client: AsyncClient,
        mock_detection_service: MagicMock,
    ):
        """Deve aceitar arquivos PNG e criar job."""
        fake_png = BytesIO(b"\x89PNG\r\n\x1a\n" + b"fake content")
        files = {"file": ("diagram.png", fake_png, "image/png")}

        response = await async_client.post(
            "/api/v1/threat-model/analyze",
            files=files,
        )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "processing"
        assert "message" in data

    async def test_analyze_returns_valid_uuid(
        self,
        async_client: AsyncClient,
        mock_detection_service: MagicMock,
    ):
        """Job ID retornado deve ser um UUID válido."""
        fake_png = BytesIO(b"\x89PNG\r\n\x1a\n" + b"fake content")
        files = {"file": ("diagram.png", fake_png, "image/png")}

        response = await async_client.post(
            "/api/v1/threat-model/analyze",
            files=files,
        )

        data = response.json()
        UUID(data["job_id"])  # deve lançar ValueError se inválido


class TestThreatModelStatus:
    """Testes de status de job."""

    async def test_status_not_found(self, async_client: AsyncClient):
        """Status deve retornar 404 para job inexistente."""
        response = await async_client.get(f"/api/v1/threat-model/{uuid4()}")
        assert response.status_code == 404

    async def test_status_completed_job(
        self,
        async_client: AsyncClient,
        db_session,
    ):
        """Status deve retornar progresso 100 para job completado."""
        job_repo = JobRepository(db_session)
        job = await job_repo.create(input_image_path="/uploads/test.png")
        await job_repo.update_status(
            job.id, JobStatus.COMPLETED, output_report_path="/reports/test.md"
        )

        response = await async_client.get(f"/api/v1/threat-model/{job.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == 100
        assert "result" in data
        assert "report_url" in data["result"]

    async def test_status_failed_job(
        self,
        async_client: AsyncClient,
        db_session,
    ):
        """Status deve retornar erro para job falho."""
        job_repo = JobRepository(db_session)
        job = await job_repo.create(input_image_path="/uploads/test.png")
        await job_repo.update_status(job.id, JobStatus.FAILED, error_message="Erro simulado")

        response = await async_client.get(f"/api/v1/threat-model/{job.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error"] == "Erro simulado"


class TestThreatModelReport:
    """Testes de geração de relatório."""

    async def test_report_not_completed(
        self,
        async_client: AsyncClient,
        db_session,
    ):
        """Relatório deve retornar 400 para job não completado."""
        job_repo = JobRepository(db_session)
        job = await job_repo.create(input_image_path="/uploads/test.png")
        await job_repo.update_status(job.id, JobStatus.PROCESSING)

        response = await async_client.get(f"/api/v1/threat-model/{job.id}/report")
        assert response.status_code == 400

    async def test_report_not_found(
        self,
        async_client: AsyncClient,
    ):
        """Relatório deve retornar 404 para job inexistente."""
        response = await async_client.get(f"/api/v1/threat-model/{uuid4()}/report")
        assert response.status_code == 404

    async def test_report_completed_returns_json(
        self,
        async_client: AsyncClient,
        db_session,
    ):
        """Relatório deve retornar JSON para job completado."""
        job_repo = JobRepository(db_session)
        job = await job_repo.create(input_image_path="/uploads/test.png")
        await job_repo.update_status(job.id, JobStatus.COMPLETED)

        response = await async_client.get(f"/api/v1/threat-model/{job.id}/report")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/json"

    async def test_report_invalid_format(
        self,
        async_client: AsyncClient,
        db_session,
    ):
        """Relatório deve rejeitar formato inválido."""
        job_repo = JobRepository(db_session)
        job = await job_repo.create(input_image_path="/uploads/test.png")
        await job_repo.update_status(job.id, JobStatus.COMPLETED)

        response = await async_client.get(f"/api/v1/threat-model/{job.id}/report?format=invalid")
        assert response.status_code == 400


class TestThreatModelPipeline:
    """Testes de integração end-to-end do pipeline assíncrono."""

    async def test_process_job_full_pipeline(
        self,
        db_session,
        mock_pipeline_services: dict[str, MagicMock],
        sample_graph: ArchitectureGraph,
        sample_threats: list[Threat],
        tmp_path: Path,
    ):
        """_process_job deve executar detecção → STRIDE → vuln → relatório e completar."""
        mock_pipeline_services["stride_instance"].analyze = AsyncMock(return_value=sample_threats)

        job_repo = JobRepository(db_session)
        job = await job_repo.create(input_image_path="/uploads/diagram.png")

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(
            "src.api.routes.threat_model.settings.storage_path",
            str(tmp_path),
        )

        def fake_generate_all(*, job, architecture_graph, threats):  # noqa: ARG001
            return _make_generated_report(str(job.id), tmp_path)

        monkeypatch.setattr(
            "src.api.routes.threat_model.report_generator.generate_all",
            fake_generate_all,
        )

        try:
            await _process_job(job.id, job.input_image_path, db_session)
        finally:
            monkeypatch.undo()

        async with AsyncSessionLocal() as check_session:
            check_repo = JobRepository(check_session)
            updated_job = await check_repo.get_by_id(job.id)
            assert updated_job is not None
            assert updated_job.status == JobStatus.COMPLETED.value
        assert updated_job.output_report_path is not None
        assert "report.json" in updated_job.output_report_path

        mock_pipeline_services["detection_service"].detect.assert_awaited_once_with(
            job.input_image_path
        )
        mock_pipeline_services["stride_instance"].analyze.assert_awaited_once_with(sample_graph)
        mock_pipeline_services["vuln_instance"].enrich.assert_awaited_once_with(sample_threats)

    async def test_status_reflects_real_threat_count(
        self,
        async_client: AsyncClient,
        db_session,
        mock_pipeline_services: dict[str, MagicMock],
        sample_threats: list[Threat],
        sample_enriched_threats: list[EnrichedThreat],
        tmp_path: Path,
    ):
        """Status deve retletir o número real de ameaças do relatório JSON."""
        mock_pipeline_services["stride_instance"].analyze = AsyncMock(return_value=sample_threats)
        mock_pipeline_services["vuln_instance"].enrich = AsyncMock(
            return_value=sample_enriched_threats
        )

        job_repo = JobRepository(db_session)
        job = await job_repo.create(input_image_path="/uploads/diagram.png")

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(
            "src.api.routes.threat_model.settings.storage_path",
            str(tmp_path),
        )

        def fake_generate_all(*, job, architecture_graph, threats):  # noqa: ARG001
            return _make_generated_report(
                str(job.id),
                tmp_path,
                threats=[{"id": t.id, "category": t.category} for t in threats],
            )

        monkeypatch.setattr(
            "src.api.routes.threat_model.report_generator.generate_all",
            fake_generate_all,
        )

        try:
            await _process_job(job.id, job.input_image_path, db_session)
        finally:
            monkeypatch.undo()

        response = await async_client.get(f"/api/v1/threat-model/{job.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["result"]["threats_count"] == len(sample_enriched_threats)

    async def test_report_reads_generated_file(
        self,
        async_client: AsyncClient,
        db_session,
        mock_pipeline_services: dict[str, MagicMock],
        sample_threats: list[Threat],
        tmp_path: Path,
    ):
        """GET /report deve ler relatório já gerado em storage."""
        mock_pipeline_services["stride_instance"].analyze = AsyncMock(return_value=sample_threats)

        job_repo = JobRepository(db_session)
        job = await job_repo.create(input_image_path="/uploads/diagram.png")

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(
            "src.api.routes.threat_model.settings.storage_path",
            str(tmp_path),
        )

        expected_data = {"job_id": str(job.id), "threats": [{"id": "t1"}]}

        def fake_generate_all(*, job, architecture_graph, threats):  # noqa: ARG001
            report = _make_generated_report(str(job.id), tmp_path, threats=expected_data["threats"])
            report.json_data = expected_data
            report.saved_paths["json"].write_text(
                json.dumps(expected_data),
                encoding="utf-8",
            )
            return report

        monkeypatch.setattr(
            "src.api.routes.threat_model.report_generator.generate_all",
            fake_generate_all,
        )

        # Garante que generate_format NÃO seja chamado (relatório existe)
        generate_format_spy = MagicMock(side_effect=AssertionError("deve usar arquivo existente"))
        monkeypatch.setattr(
            "src.api.routes.threat_model.report_generator.generate_format",
            generate_format_spy,
        )

        try:
            await _process_job(job.id, job.input_image_path, db_session)
        finally:
            monkeypatch.undo()

        response = await async_client.get(f"/api/v1/threat-model/{job.id}/report?format=json")
        assert response.status_code == 200
        assert response.json() == expected_data
        generate_format_spy.assert_not_called()

    async def test_report_fallback_on_missing_file(
        self,
        async_client: AsyncClient,
        db_session,
        tmp_path: Path,
    ):
        """GET /report deve gerar sob demanda quando arquivo não existe."""
        job_repo = JobRepository(db_session)
        job = await job_repo.create(input_image_path="/uploads/diagram.png")
        await job_repo.update_status(job.id, JobStatus.COMPLETED)

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(
            "src.api.routes.threat_model.settings.storage_path",
            str(tmp_path),
        )

        expected_data = {"job_id": str(job.id), "threats": []}
        generate_format_spy = MagicMock(return_value=(expected_data, "application/json"))
        monkeypatch.setattr(
            "src.api.routes.threat_model.report_generator.generate_format",
            generate_format_spy,
        )

        try:
            response = await async_client.get(f"/api/v1/threat-model/{job.id}/report?format=json")
        finally:
            monkeypatch.undo()

        assert response.status_code == 200
        assert response.json() == expected_data
        generate_format_spy.assert_called_once()

    async def test_analyze_starts_background_job(
        self,
        async_client: AsyncClient,
        mock_pipeline_services: dict[str, MagicMock],
        tmp_path: Path,
    ):
        """POST /analyze deve retornar 202 e iniciar job de processamento."""
        mock_pipeline_services["stride_instance"].analyze = AsyncMock(return_value=[])

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(
            "src.api.routes.threat_model.settings.storage_path",
            str(tmp_path),
        )
        monkeypatch.setattr(
            "src.api.routes.threat_model.report_generator.generate_all",
            lambda *, job, architecture_graph, threats: _make_generated_report(  # noqa: ARG001
                str(job.id), tmp_path
            ),
        )

        # Torna a tarefa em background síncrona para testar o resultado final.
        created_tasks: list[asyncio.Task] = []
        original_create_task = asyncio.create_task

        def tracked_create_task(coro, *, name=None):  # noqa: ARG001
            task = original_create_task(coro, name=name)
            created_tasks.append(task)
            return task

        monkeypatch.setattr(
            "src.api.routes.threat_model.asyncio.create_task",
            tracked_create_task,
        )

        try:
            fake_png = BytesIO(b"\x89PNG\r\n\x1a\n" + b"fake content")
            files = {"file": ("diagram.png", fake_png, "image/png")}
            response = await async_client.post(
                "/api/v1/threat-model/analyze",
                files=files,
            )

            assert response.status_code == 202
            data = response.json()
            job_id = data["job_id"]

            # Aguarda a tarefa em background concluir antes de consultar status.
            if created_tasks:
                await asyncio.gather(*created_tasks, return_exceptions=True)

            status_response = await async_client.get(f"/api/v1/threat-model/{job_id}")
            status_data = status_response.json()
            assert status_data["status"] in {"completed", "failed"}
        finally:
            monkeypatch.undo()
