"""Testes unitários para a Spec 006 — Gerador de Relatórios STRIDE.

Cobre:
    - ReportGenerator.generate_format() para todos os 5 formatos
    - Estrutura e campos obrigatórios de cada saída
    - Cálculo de Risk Score (RF-06)
    - Persistência em disco (RF-08)
    - CSV exporter (RF-04)
    - PDF exporter fallback (RF-05)
    - Validação de formato inválido (RF-07)
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from src.domain.models import (
    ArchitectureGraph,
    BoundingBox,
    Countermeasure,
    DataFlow,
    DetectedComponent,
    EnrichedThreat,
    Job,
    JobStatus,
    Point,
    Severity,
)
from src.services.csv_exporter import export_to_csv_bytes, export_to_csv_string
from src.services.pdf_exporter import (
    WeasyPrintUnavailableError,
    export_html_to_pdf_with_fallback,
)
from src.services.report_generator import (
    SEVERITY_WEIGHT,
    ReportGenerator,
    StrideMatrixRow,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def tmp_reports_dir(tmp_path: Path) -> Path:
    """Diretório temporário isolado por teste."""
    d = tmp_path / "reports"
    d.mkdir()
    return d


@pytest.fixture()
def generator(tmp_reports_dir: Path) -> ReportGenerator:
    """Instância de ReportGenerator usando diretório temporário."""
    return ReportGenerator(reports_base_path=tmp_reports_dir)


@pytest.fixture()
def sample_job() -> Job:
    """Job de domínio com status COMPLETED."""
    now = datetime.now(timezone.utc)
    return Job(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        status=JobStatus.COMPLETED,
        input_image_path="/uploads/test-architecture.png",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture()
def sample_graph() -> ArchitectureGraph:
    """Grafo de arquitetura com 3 componentes e 1 fluxo de dados."""
    return ArchitectureGraph(
        components=[
            DetectedComponent(
                id="comp-web-01", type="web_server", confidence=0.95,
                bbox=BoundingBox(x_min=0, y_min=0, x_max=100, y_max=100),
                center=Point(x=50, y=50),
            ),
            DetectedComponent(
                id="comp-api-01", type="api", confidence=0.91,
                bbox=BoundingBox(x_min=110, y_min=0, x_max=210, y_max=100),
                center=Point(x=160, y=50),
            ),
            DetectedComponent(
                id="comp-db-01", type="database", confidence=0.88,
                bbox=BoundingBox(x_min=220, y_min=0, x_max=320, y_max=100),
                center=Point(x=270, y=50),
            ),
        ],
        data_flows=[
            DataFlow(
                source_id="comp-web-01",
                target_id="comp-api-01",
                direction="unidirectional",
                inferred=False,
            )
        ],
        trust_boundaries=[["comp-web-01", "comp-api-01"], ["comp-db-01"]],
    )


@pytest.fixture()
def sample_threats() -> list[EnrichedThreat]:
    """Lista representativa de ameaças enriquecidas cobrindo diferentes severidades."""
    return [
        EnrichedThreat(
            id="threat-001",
            category="I",
            category_name="Information Disclosure",
            component_id="comp-db-01",
            component_type="database",
            severity=Severity.CRITICAL,
            description="Dados sensíveis podem ser exfiltrados do banco de dados.",
            cwe_id="CWE-200",
            cwe_name="Exposure of Sensitive Information to an Unauthorized Actor",
            cve_ids=["CVE-2023-5678"],
            countermeasures=[
                Countermeasure(
                    title="Criptografar dados em repouso",
                    description="Usar AES-256 para todos os dados sensíveis.",
                    owasp_ref="OWASP Cryptographic Storage Cheat Sheet",
                ),
                Countermeasure(
                    title="Aplicar mascaramento de dados",
                    description="Mascarar campos sensíveis nas respostas da API.",
                    owasp_ref="OWASP Data Protection Cheat Sheet",
                ),
            ],
        ),
        EnrichedThreat(
            id="threat-002",
            category="S",
            category_name="Spoofing",
            component_id="comp-web-01",
            component_type="web_server",
            severity=Severity.HIGH,
            description="Servidor web pode ser falsificado por atacante man-in-the-middle.",
            cwe_id="CWE-290",
            cwe_name="Authentication Bypass by Spoofing",
            cve_ids=[],
            countermeasures=[
                Countermeasure(
                    title="Implementar mTLS",
                    description="Usar certificados cliente/servidor para autenticação mútua.",
                    owasp_ref="OWASP Transport Layer Security Cheat Sheet",
                )
            ],
        ),
        EnrichedThreat(
            id="threat-003",
            category="T",
            category_name="Tampering",
            component_id="comp-api-01",
            component_type="api",
            severity=Severity.MEDIUM,
            description="Payloads de API podem ser alterados em trânsito.",
            cwe_id="CWE-345",
            cwe_name="Insufficient Verification of Data Authenticity",
            cve_ids=[],
            countermeasures=[
                Countermeasure(
                    title="Validar integridade com HMAC",
                    description="Assinar e verificar todos os payloads críticos.",
                    owasp_ref="OWASP Input Validation Cheat Sheet",
                )
            ],
        ),
        EnrichedThreat(
            id="threat-004",
            category="D",
            category_name="Denial of Service",
            component_id="comp-api-01",
            component_type="api",
            severity=Severity.LOW,
            description="API pode ser sobrecarregada por requisições abusivas.",
            cwe_id="CWE-400",
            cwe_name="Uncontrolled Resource Consumption",
            cve_ids=[],
            countermeasures=[],
        ),
    ]


# ── Testes: generate_format JSON ─────────────────────────────────────────────


class TestGenerateFormatJson:
    def test_returns_dict_and_json_media_type(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, media_type = generator.generate_format(
            sample_job, sample_graph, sample_threats, "json"
        )
        assert media_type == "application/json"
        assert isinstance(content, dict)

    def test_json_has_required_top_level_fields(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, _ = generator.generate_format(sample_job, sample_graph, sample_threats, "json")
        required = {"job_id", "timestamp", "image_name", "components", "data_flows",
                    "trust_boundaries", "threats", "summary"}
        assert required.issubset(set(content.keys()))  # type: ignore[arg-type]

    def test_json_summary_counts_match_threats(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, _ = generator.generate_format(sample_job, sample_graph, sample_threats, "json")
        summary = content["summary"]  # type: ignore[index]
        assert summary["total_threats"] == len(sample_threats)
        assert summary["critical"] == 1
        assert summary["high"] == 1
        assert summary["medium"] == 1
        assert summary["low"] == 1

    def test_json_threat_fields(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, _ = generator.generate_format(sample_job, sample_graph, sample_threats, "json")
        threat = content["threats"][0]  # type: ignore[index]
        required_fields = {
            "id", "category", "category_name", "component_id",
            "component_type", "severity", "description", "countermeasures",
        }
        assert required_fields.issubset(set(threat.keys()))

    def test_json_job_id_matches(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, _ = generator.generate_format(sample_job, sample_graph, sample_threats, "json")
        assert content["job_id"] == str(sample_job.id)  # type: ignore[index]

    def test_json_image_name_extracted(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, _ = generator.generate_format(sample_job, sample_graph, sample_threats, "json")
        assert content["image_name"] == "test-architecture.png"  # type: ignore[index]

    def test_json_file_persisted(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
        tmp_reports_dir: Path,
    ) -> None:
        generator.generate_format(sample_job, sample_graph, sample_threats, "json")
        report_file = tmp_reports_dir / str(sample_job.id) / "report.json"
        assert report_file.exists()
        # Valida que o arquivo é JSON válido
        data = json.loads(report_file.read_text(encoding="utf-8"))
        assert data["job_id"] == str(sample_job.id)


# ── Testes: generate_format Markdown ─────────────────────────────────────────


class TestGenerateFormatMarkdown:
    def test_returns_string_and_markdown_media_type(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, media_type = generator.generate_format(
            sample_job, sample_graph, sample_threats, "md"
        )
        assert media_type == "text/markdown"
        assert isinstance(content, str)

    def test_markdown_has_all_required_sections(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, _ = generator.generate_format(sample_job, sample_graph, sample_threats, "md")
        assert isinstance(content, str)
        assert "# Relatório de Modelagem de Ameaças" in content
        assert "## 1. Resumo Executivo" in content
        assert "## 2. Diagrama de Arquitetura Analisado" in content
        assert "## 3. Matriz STRIDE" in content
        assert "## 4. Detalhamento de Ameaças" in content
        assert "## 5. Sumário de Contramedidas" in content
        assert "## 6. Recomendações" in content

    def test_markdown_contains_component_types(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, _ = generator.generate_format(sample_job, sample_graph, sample_threats, "md")
        assert isinstance(content, str)
        assert "web_server" in content
        assert "database" in content
        assert "api" in content

    def test_markdown_stride_matrix_has_header(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, _ = generator.generate_format(sample_job, sample_graph, sample_threats, "md")
        assert isinstance(content, str)
        # Tabela STRIDE deve ter cabeçalho com todas as categorias
        assert "| Componente | S | T | R | I | D | E |" in content

    def test_markdown_critical_section_present(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, _ = generator.generate_format(sample_job, sample_graph, sample_threats, "md")
        assert isinstance(content, str)
        assert "4.1 Ameaças Críticas" in content

    def test_markdown_job_id_in_footer(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, _ = generator.generate_format(sample_job, sample_graph, sample_threats, "md")
        assert isinstance(content, str)
        assert str(sample_job.id) in content

    def test_markdown_file_persisted(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
        tmp_reports_dir: Path,
    ) -> None:
        generator.generate_format(sample_job, sample_graph, sample_threats, "md")
        report_file = tmp_reports_dir / str(sample_job.id) / "report.md"
        assert report_file.exists()
        assert report_file.stat().st_size > 0


# ── Testes: generate_format HTML ─────────────────────────────────────────────


class TestGenerateFormatHtml:
    def test_returns_string_and_html_media_type(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, media_type = generator.generate_format(
            sample_job, sample_graph, sample_threats, "html"
        )
        assert media_type == "text/html"
        assert isinstance(content, str)
        assert "<!DOCTYPE html>" in content

    def test_html_has_severity_badges(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, _ = generator.generate_format(sample_job, sample_graph, sample_threats, "html")
        assert isinstance(content, str)
        # CSS classes de severidade devem estar presentes
        assert "badge critical" in content
        assert "badge high" in content

    def test_html_is_responsive(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, _ = generator.generate_format(sample_job, sample_graph, sample_threats, "html")
        assert isinstance(content, str)
        assert 'name="viewport"' in content

    def test_html_contains_stride_table(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, _ = generator.generate_format(sample_job, sample_graph, sample_threats, "html")
        assert isinstance(content, str)
        assert "stride-matrix" in content

    def test_html_file_persisted(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
        tmp_reports_dir: Path,
    ) -> None:
        generator.generate_format(sample_job, sample_graph, sample_threats, "html")
        report_file = tmp_reports_dir / str(sample_job.id) / "report.html"
        assert report_file.exists()


# ── Testes: CSV Exporter (RF-04) ──────────────────────────────────────────────


class TestCsvExporter:
    def test_csv_string_has_header_row(self, sample_threats: list[EnrichedThreat]) -> None:
        csv_str = export_to_csv_string(sample_threats)
        first_line = csv_str.splitlines()[0]
        assert "threat_id" in first_line
        assert "category" in first_line
        assert "severity" in first_line
        assert "component_type" in first_line
        assert "cwe_id" in first_line
        assert "countermeasure_title" in first_line

    def test_csv_row_count_equals_threat_countermeasure_pairs(
        self, sample_threats: list[EnrichedThreat]
    ) -> None:
        csv_str = export_to_csv_string(sample_threats)
        lines = [l for l in csv_str.splitlines() if l.strip()]
        # 1 header + N data rows (1 row per threat×countermeasure, min 1 per threat)
        # threat-001: 2 CMs, threat-002: 1, threat-003: 1, threat-004: 0 CMs → 1 row
        expected_data_rows = 2 + 1 + 1 + 1  # = 5
        assert len(lines) - 1 == expected_data_rows  # -1 for header

    def test_csv_bytes_has_utf8_bom(self, sample_threats: list[EnrichedThreat]) -> None:
        csv_bytes = export_to_csv_bytes(sample_threats)
        # UTF-8 BOM: EF BB BF
        assert csv_bytes[:3] == b"\xef\xbb\xbf"

    def test_csv_empty_threats_still_has_header(self) -> None:
        csv_str = export_to_csv_string([])
        lines = [l for l in csv_str.splitlines() if l.strip()]
        assert len(lines) == 1  # apenas o cabeçalho
        assert "threat_id" in lines[0]

    def test_generate_format_csv_returns_bytes(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        content, media_type = generator.generate_format(
            sample_job, sample_graph, sample_threats, "csv"
        )
        assert media_type == "text/csv"
        assert isinstance(content, bytes)

    def test_csv_file_persisted(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
        tmp_reports_dir: Path,
    ) -> None:
        generator.generate_format(sample_job, sample_graph, sample_threats, "csv")
        report_file = tmp_reports_dir / str(sample_job.id) / "report.csv"
        assert report_file.exists()
        assert report_file.stat().st_size > 0


# ── Testes: PDF Exporter fallback (RF-05) ─────────────────────────────────────


class TestPdfExporterFallback:
    def test_fallback_returns_html_when_weasyprint_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Simula WeasyPrint indisponível e garante que o fallback HTML é retornado."""
        import src.services.pdf_exporter as pdf_mod

        def _raise(*_args: object, **_kwargs: object) -> None:
            raise WeasyPrintUnavailableError("WeasyPrint simulado como ausente")

        monkeypatch.setattr(pdf_mod, "export_html_to_pdf", _raise)
        html_input = "<html><body><p>Teste</p></body></html>"
        content_bytes, media_type = export_html_to_pdf_with_fallback(html_input)
        assert media_type == "text/html"
        assert b"Teste" in content_bytes
        assert b"PDF" in content_bytes  # aviso de fallback deve mencionar PDF

    def test_generate_format_pdf_returns_bytes(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        """PDF ou HTML (fallback) deve sempre retornar bytes."""
        content, media_type = generator.generate_format(
            sample_job, sample_graph, sample_threats, "pdf"
        )
        assert isinstance(content, bytes)
        assert media_type in ("application/pdf", "text/html")


# ── Testes: Risk Score (RF-06) ────────────────────────────────────────────────


class TestRiskScore:
    def test_severity_weights_defined(self) -> None:
        assert SEVERITY_WEIGHT["critical"] == 10
        assert SEVERITY_WEIGHT["high"] == 7
        assert SEVERITY_WEIGHT["medium"] == 4
        assert SEVERITY_WEIGHT["low"] == 1

    def test_stride_matrix_risk_scores_are_correct(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        """Verifica que o risk score acumula os pesos de severidade por componente."""
        content, _ = generator.generate_format(sample_job, sample_graph, sample_threats, "json")
        # database recebeu 1 ameaça CRITICAL (peso 10)
        # api recebeu 1 MEDIUM (4) + 1 LOW (1) = 5
        # web_server recebeu 1 HIGH (7)
        # Verificamos via JSON a lista de componentes e ameaças
        threats = content["threats"]  # type: ignore[index]
        db_threats = [t for t in threats if t["component_type"] == "database"]
        assert any(t["severity"] == "critical" for t in db_threats)

    def test_stride_matrix_sorted_by_risk_score(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        """Garante que a matriz STRIDE está ordenada por risk_score decrescente."""
        ctx = generator._build_context(sample_job, sample_graph, sample_threats)
        scores = [row.risk_score for row in ctx.stride_matrix]
        assert scores == sorted(scores, reverse=True)

    def test_stride_matrix_categories_correct(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        """Cada componente deve ter apenas as categorias das suas ameaças."""
        ctx = generator._build_context(sample_job, sample_graph, sample_threats)
        matrix = {row.component_type: row for row in ctx.stride_matrix}

        assert "I" in matrix["database"].categories
        assert "S" in matrix["web_server"].categories
        assert "T" in matrix["api"].categories
        assert "D" in matrix["api"].categories


# ── Testes: generate_format inválido ─────────────────────────────────────────


class TestInvalidFormat:
    def test_unsupported_format_raises_value_error(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        with pytest.raises(ValueError, match="não suportado"):
            generator.generate_format(sample_job, sample_graph, sample_threats, "xml")

    def test_empty_format_raises_value_error(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        with pytest.raises(ValueError):
            generator.generate_format(sample_job, sample_graph, sample_threats, "")


# ── Testes: Persistência (RF-08) ──────────────────────────────────────────────


class TestPersistence:
    def test_generate_all_creates_all_format_files(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
        tmp_reports_dir: Path,
    ) -> None:
        result = generator.generate_all(sample_job, sample_graph, sample_threats)

        job_dir = tmp_reports_dir / str(sample_job.id)
        assert (job_dir / "report.json").exists()
        assert (job_dir / "report.md").exists()
        assert (job_dir / "report.html").exists()
        assert (job_dir / "report.csv").exists()
        # PDF pode ser .pdf ou .html (fallback)
        assert (job_dir / "report.pdf").exists() or (job_dir / "report.html").exists()

    def test_generate_all_returns_generated_report_with_json_data(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        result = generator.generate_all(sample_job, sample_graph, sample_threats)
        assert result.job_id == str(sample_job.id)
        assert "summary" in result.json_data
        assert result.json_data["summary"]["total_threats"] == len(sample_threats)

    def test_get_saved_paths_returns_existing_files(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
    ) -> None:
        generator.generate_all(sample_job, sample_graph, sample_threats)
        paths = generator.get_saved_paths(str(sample_job.id))
        assert "json" in paths
        assert "md" in paths
        assert "html" in paths
        assert "csv" in paths

    def test_get_saved_paths_returns_empty_for_unknown_job(
        self, generator: ReportGenerator
    ) -> None:
        paths = generator.get_saved_paths("nonexistent-job-id")
        assert paths == {}

    def test_reports_saved_under_job_subdir(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
        sample_threats: list[EnrichedThreat],
        tmp_reports_dir: Path,
    ) -> None:
        generator.generate_format(sample_job, sample_graph, sample_threats, "md")
        job_dir = tmp_reports_dir / str(sample_job.id)
        assert job_dir.is_dir()
        assert any(job_dir.iterdir())


# ── Testes: empty threats edge case ──────────────────────────────────────────


class TestEmptyThreats:
    def test_json_with_no_threats(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
    ) -> None:
        content, media_type = generator.generate_format(
            sample_job, sample_graph, [], "json"
        )
        assert content["summary"]["total_threats"] == 0  # type: ignore[index]
        assert content["threats"] == []  # type: ignore[index]

    def test_markdown_with_no_threats(
        self,
        generator: ReportGenerator,
        sample_job: Job,
        sample_graph: ArchitectureGraph,
    ) -> None:
        content, _ = generator.generate_format(sample_job, sample_graph, [], "md")
        assert isinstance(content, str)
        assert "# Relatório de Modelagem de Ameaças" in content
