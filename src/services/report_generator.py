"""Gerador de relatórios de modelagem de ameaças STRIDE (Spec 006).

Orquestra todos os formatos de saída:
    - JSON  (RF-02) — estrutura completa, inline
    - Markdown (RF-01) — via template Jinja2
    - HTML (RF-03) — via template Jinja2
    - CSV  (RF-04) — via pandas
    - PDF  (RF-05) — via WeasyPrint (com fallback HTML)

Também:
    - Calcula Risk Score por componente (RF-06)
    - Persiste todos os formatos em reports/{job_id}/ (RF-08)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.core.config import settings
from src.core.logging import get_logger
from src.domain.models import ArchitectureGraph, EnrichedThreat, Job, Severity
from src.services.csv_exporter import export_to_csv_bytes
from src.services.pdf_exporter import export_html_to_pdf_with_fallback

logger = get_logger(__name__)

# ── Constantes ───────────────────────────────────────────────────────────────

STRIDE_NAMES: dict[str, str] = {
    "S": "Spoofing",
    "T": "Tampering",
    "R": "Repudiation",
    "I": "Information Disclosure",
    "D": "Denial of Service",
    "E": "Elevation of Privilege",
}

SEVERITY_ORDER: list[str] = ["critical", "high", "medium", "low", "info"]

# RF-06: pesos de severidade para cálculo do Risk Score
SEVERITY_WEIGHT: dict[str, int] = {
    "critical": 10,
    "high": 7,
    "medium": 4,
    "low": 1,
    "info": 0,
}

_TEMPLATES_DIR = Path(__file__).parent.parent / "core" / "templates"


# ── Data classes auxiliares ───────────────────────────────────────────────────

@dataclass
class StrideMatrixRow:
    """Linha da matriz STRIDE para um componente."""

    component_type: str
    categories: set[str] = field(default_factory=set)
    risk_score: int = 0


@dataclass
class CountermeasureSummaryItem:
    """Item da tabela consolidada de contramedidas."""

    threat_id: str
    severity: str
    component_type: str
    title: str
    description: str
    owasp_ref: str | None


@dataclass
class Recommendation:
    """Recomendação de hardening derivada de ameaças críticas/altas."""

    title: str
    component_type: str
    description: str


@dataclass
class ReportContext:
    """Contexto completo usado por todos os templates."""

    job_id: str
    timestamp: str
    image_name: str
    component_count: int
    threat_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    components: list[Any]
    data_flows: list[Any]
    trust_boundaries: list[Any]
    stride_matrix: list[StrideMatrixRow]
    stride_names: dict[str, str]
    critical_threats: list[EnrichedThreat]
    high_threats: list[EnrichedThreat]
    medium_threats: list[EnrichedThreat]
    low_threats: list[EnrichedThreat]
    countermeasures_summary: list[CountermeasureSummaryItem]
    top_recommendations: list[Recommendation]


@dataclass
class GeneratedReport:
    """Resultado completo de uma geração de relatório.

    Contém os arquivos gerados e a estrutura JSON para resposta inline.
    """

    job_id: str
    saved_paths: dict[str, Path]   # {"md": Path, "json": Path, ...}
    json_data: dict[str, Any]


# ── ReportGenerator ───────────────────────────────────────────────────────────

class ReportGenerator:
    """Orquestra a geração de relatórios em todos os formatos suportados."""

    def __init__(self, reports_base_path: str | Path | None = None) -> None:
        """Inicializa o gerador.

        Args:
            reports_base_path: Diretório raiz para persistência dos relatórios.
                Default: {settings.storage_path}/reports
        """
        if reports_base_path is None:
            self._reports_root = Path(settings.storage_path) / "reports"
        else:
            self._reports_root = Path(reports_base_path)

        self._reports_root.mkdir(parents=True, exist_ok=True)
        self._jinja_env = self._build_jinja_env()

    # ── Jinja2 setup ─────────────────────────────────────────────────────────

    def _build_jinja_env(self) -> Environment:
        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Template MD não deve ter auto-escape (markdown usa < > livremente)
        env.globals["enumerate"] = enumerate
        return env

    def _get_md_env(self) -> Environment:
        """Retorna ambiente Jinja2 sem autoescape para templates Markdown."""
        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        env.globals["enumerate"] = enumerate
        return env

    # ── Context builder ───────────────────────────────────────────────────────

    def _build_context(
        self,
        job: Job,
        architecture_graph: ArchitectureGraph,
        threats: list[EnrichedThreat],
    ) -> ReportContext:
        """Monta o contexto de template a partir dos dados de entrada."""
        image_name = Path(job.input_image_path).name if job.input_image_path else "N/A"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Grupos por severidade
        critical = [t for t in threats if t.severity == Severity.CRITICAL]
        high = [t for t in threats if t.severity == Severity.HIGH]
        medium = [t for t in threats if t.severity == Severity.MEDIUM]
        low = [t for t in threats if t.severity == Severity.LOW]

        # RF-06: matriz STRIDE e risk scores por componente
        matrix_map: dict[str, StrideMatrixRow] = {}
        for threat in threats:
            ctype = threat.component_type
            if ctype not in matrix_map:
                matrix_map[ctype] = StrideMatrixRow(component_type=ctype)
            row = matrix_map[ctype]
            row.categories.add(threat.category)
            row.risk_score += SEVERITY_WEIGHT.get(threat.severity.value, 0)

        stride_matrix = sorted(
            matrix_map.values(), key=lambda r: r.risk_score, reverse=True
        )

        # Tabela consolidada de contramedidas (ordenada por severidade)
        severity_priority = {s: i for i, s in enumerate(SEVERITY_ORDER)}
        cm_summary: list[CountermeasureSummaryItem] = []
        for threat in sorted(threats, key=lambda t: severity_priority.get(t.severity.value, 99)):
            for cm in threat.countermeasures:
                cm_summary.append(
                    CountermeasureSummaryItem(
                        threat_id=threat.id,
                        severity=threat.severity.value,
                        component_type=threat.component_type,
                        title=cm.title,
                        description=cm.description,
                        owasp_ref=cm.owasp_ref,
                    )
                )

        # Top 3 recomendações: contramedidas das ameaças críticas/altas
        top_threats = (critical + high)[:3]
        top_recs: list[Recommendation] = []
        for threat in top_threats:
            if threat.countermeasures:
                cm = threat.countermeasures[0]
                top_recs.append(
                    Recommendation(
                        title=cm.title,
                        component_type=threat.component_type,
                        description=cm.description,
                    )
                )
            else:
                top_recs.append(
                    Recommendation(
                        title=f"Mitigar {STRIDE_NAMES.get(threat.category, threat.category)}",
                        component_type=threat.component_type,
                        description=threat.description,
                    )
                )

        return ReportContext(
            job_id=str(job.id),
            timestamp=timestamp,
            image_name=image_name,
            component_count=len(architecture_graph.components),
            threat_count=len(threats),
            critical_count=len(critical),
            high_count=len(high),
            medium_count=len(medium),
            low_count=len(low),
            components=architecture_graph.components,
            data_flows=architecture_graph.data_flows,
            trust_boundaries=architecture_graph.trust_boundaries,
            stride_matrix=stride_matrix,
            stride_names=STRIDE_NAMES,
            critical_threats=critical,
            high_threats=high,
            medium_threats=medium,
            low_threats=low,
            countermeasures_summary=cm_summary,
            top_recommendations=top_recs,
        )

    # ── Individual renderers ──────────────────────────────────────────────────

    def _render_json(self, ctx: ReportContext, threats: list[EnrichedThreat]) -> dict[str, Any]:
        """RF-02: Estrutura JSON completa."""
        return {
            "job_id": ctx.job_id,
            "timestamp": ctx.timestamp,
            "image_name": ctx.image_name,
            "components": [c.model_dump() for c in ctx.components],
            "data_flows": [f.model_dump() for f in ctx.data_flows],
            "trust_boundaries": ctx.trust_boundaries,
            "threats": [
                {
                    "id": t.id,
                    "category": t.category,
                    "category_name": STRIDE_NAMES.get(t.category, t.category),
                    "component_id": t.component_id,
                    "component_type": t.component_type,
                    "severity": t.severity.value,
                    "description": t.description,
                    "cwe_id": t.cwe_id,
                    "cwe_name": t.cwe_name,
                    "cve_ids": t.cve_ids,
                    "countermeasures": [
                        {
                            "title": cm.title,
                            "description": cm.description,
                            "owasp_ref": cm.owasp_ref,
                        }
                        for cm in t.countermeasures
                    ],
                }
                for t in threats
            ],
            "summary": {
                "total_threats": ctx.threat_count,
                "critical": ctx.critical_count,
                "high": ctx.high_count,
                "medium": ctx.medium_count,
                "low": ctx.low_count,
            },
        }

    def _render_markdown(self, ctx: ReportContext) -> str:
        """RF-01: Relatório Markdown via template Jinja2."""
        template = self._get_md_env().get_template("stride_report.md.j2")
        return template.render(**ctx.__dict__)

    def _render_html(self, ctx: ReportContext) -> str:
        """RF-03: Relatório HTML via template Jinja2."""
        template = self._jinja_env.get_template("stride_report.html.j2")
        return template.render(**ctx.__dict__)

    def _render_csv(self, threats: list[EnrichedThreat]) -> bytes:
        """RF-04: Relatório CSV via pandas."""
        return export_to_csv_bytes(threats)

    def _render_pdf(self, html_content: str) -> tuple[bytes, str]:
        """RF-05: Relatório PDF via WeasyPrint (ou fallback HTML)."""
        return export_html_to_pdf_with_fallback(html_content)

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self, job_id: str, ext: str, content: bytes | str) -> Path:
        """Persiste um artefato de relatório em reports/{job_id}/.{ext}.

        Args:
            job_id: ID do job (usado como nome de subpasta e arquivo).
            ext: Extensão sem ponto (ex: "md", "json").
            content: Conteúdo a persistir.

        Returns:
            Path: Caminho absoluto do arquivo salvo.
        """
        job_dir = self._reports_root / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        file_path = job_dir / f"report.{ext}"

        if isinstance(content, str):
            file_path.write_text(content, encoding="utf-8")
        else:
            file_path.write_bytes(content)

        logger.debug(f"Relatório salvo: {file_path}")
        return file_path

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_all(
        self,
        job: Job,
        architecture_graph: ArchitectureGraph,
        threats: list[EnrichedThreat],
    ) -> GeneratedReport:
        """Gera e persiste todos os formatos de relatório (RF-08).

        Args:
            job: Metadados do job de análise.
            architecture_graph: Grafo de componentes e fluxos detectados.
            threats: Lista de ameaças enriquecidas com vulnerabilidades.

        Returns:
            GeneratedReport: Caminhos de todos os arquivos gerados + dados JSON.
        """
        job_id = str(job.id)
        ctx = self._build_context(job, architecture_graph, threats)
        logger.info(f"Gerando relatórios para job {job_id} ({ctx.threat_count} ameaças)")

        saved: dict[str, Path] = {}

        # JSON
        json_data = self._render_json(ctx, threats)
        saved["json"] = self._save(job_id, "json", json.dumps(json_data, ensure_ascii=False, indent=2))

        # Markdown
        md_content = self._render_markdown(ctx)
        saved["md"] = self._save(job_id, "md", md_content)

        # HTML
        html_content = self._render_html(ctx)
        saved["html"] = self._save(job_id, "html", html_content)

        # CSV
        csv_bytes = self._render_csv(threats)
        saved["csv"] = self._save(job_id, "csv", csv_bytes)

        # PDF (com fallback)
        pdf_bytes, pdf_media_type = self._render_pdf(html_content)
        ext = "pdf" if pdf_media_type == "application/pdf" else "html"
        saved["pdf"] = self._save(job_id, ext, pdf_bytes)
        if ext != "pdf":
            logger.warning(f"Job {job_id}: PDF indisponível, salvo fallback HTML em report.{ext}")

        logger.info(f"Job {job_id}: {len(saved)} artefatos gerados — {list(saved.keys())}")
        return GeneratedReport(job_id=job_id, saved_paths=saved, json_data=json_data)

    def generate_format(
        self,
        job: Job,
        architecture_graph: ArchitectureGraph,
        threats: list[EnrichedThreat],
        fmt: str,
    ) -> tuple[bytes | str | dict, str]:
        """Gera apenas o formato solicitado e persiste o arquivo.

        Args:
            job: Metadados do job.
            architecture_graph: Grafo de arquitetura.
            threats: Ameaças enriquecidas.
            fmt: Formato desejado — "json" | "md" | "html" | "csv" | "pdf".

        Returns:
            tuple[content, media_type]:
                - "json"  → (dict, "application/json")
                - "md"    → (str,  "text/markdown")
                - "html"  → (str,  "text/html")
                - "csv"   → (bytes, "text/csv")
                - "pdf"   → (bytes, "application/pdf") ou (bytes, "text/html") no fallback

        Raises:
            ValueError: Se o formato não for suportado.
        """
        supported = {"json", "md", "html", "csv", "pdf"}
        if fmt not in supported:
            raise ValueError(
                f"Formato '{fmt}' não suportado. Use um de: {', '.join(sorted(supported))}"
            )

        job_id = str(job.id)
        ctx = self._build_context(job, architecture_graph, threats)

        match fmt:
            case "json":
                data = self._render_json(ctx, threats)
                self._save(job_id, "json", json.dumps(data, ensure_ascii=False, indent=2))
                return data, "application/json"

            case "md":
                content = self._render_markdown(ctx)
                self._save(job_id, "md", content)
                return content, "text/markdown"

            case "html":
                content = self._render_html(ctx)
                self._save(job_id, "html", content)
                return content, "text/html"

            case "csv":
                content_bytes = self._render_csv(threats)
                self._save(job_id, "csv", content_bytes)
                return content_bytes, "text/csv"

            case "pdf":
                html_content = self._render_html(ctx)
                self._save(job_id, "html", html_content)  # salva HTML também
                pdf_bytes, media_type = self._render_pdf(html_content)
                ext = "pdf" if media_type == "application/pdf" else "html"
                self._save(job_id, ext, pdf_bytes)
                return pdf_bytes, media_type

            case _:  # pragma: no cover
                raise ValueError(f"Formato inesperado: {fmt}")

    def get_saved_paths(self, job_id: str) -> dict[str, Path]:
        """Retorna os arquivos já persistidos para um dado job_id.

        Args:
            job_id: UUID do job (string).

        Returns:
            dict[str, Path]: Mapeamento extensão → caminho absoluto, apenas
                para arquivos que existem em disco.
        """
        job_dir = self._reports_root / job_id
        result: dict[str, Path] = {}
        for ext in ("json", "md", "html", "csv", "pdf"):
            p = job_dir / f"report.{ext}"
            if p.exists():
                result[ext] = p
        return result


# Singleton para reutilização em toda a aplicação
report_generator = ReportGenerator()
