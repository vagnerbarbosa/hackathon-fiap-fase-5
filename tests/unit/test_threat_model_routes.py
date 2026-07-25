"""Testes para rotas de threat model da API."""

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.main import app
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
)
from src.infrastructure.repositories.job_repository import JobRepository


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

    async def test_analyze_rejects_unsupported_image_type(
        self, async_client: AsyncClient
    ):
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
        await job_repo.update_status(
            job.id, JobStatus.FAILED, error_message="Erro simulado"
        )

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

        response = await async_client.get(
            f"/api/v1/threat-model/{job.id}/report?format=invalid"
        )
        assert response.status_code == 400
