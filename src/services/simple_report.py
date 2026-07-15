"""Gerador simples de relatórios HTML para testes locais."""

from datetime import datetime
from typing import Any

from src.domain.models import ArchitectureGraph, EnrichedThreat, Severity


class SimpleHTMLReportGenerator:
    """Gera relatórios HTML simples para testes locais."""

    def generate(
        self,
        job_id: str,
        architecture_graph: ArchitectureGraph,
        threats: list[EnrichedThreat],
    ) -> str:
        """Gera relatório HTML completo.

        Args:
            job_id: ID do job.
            architecture_graph: Grafo de arquitetura.
            threats: Lista de ameaças enriquecidas.

        Returns:
            str: HTML do relatório.
        """
        # Agrupar ameaças por severidade
        critical = [t for t in threats if t.severity == Severity.CRITICAL]
        high = [t for t in threats if t.severity == Severity.HIGH]
        medium = [t for t in threats if t.severity == Severity.MEDIUM]
        low = [t for t in threats if t.severity == Severity.LOW]
        info = [t for t in threats if t.severity == Severity.INFO]

        # Agrupar por categoria STRIDE
        stride_categories = {"S": "Spoofing", "T": "Tampering", "R": "Repudiation",
                            "I": "Information Disclosure", "D": "Denial of Service",
                            "E": "Elevation of Privilege"}

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório STRIDE - {job_id[:8]}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2rem; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            padding: 30px;
            background: #f8fafc;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            color: #1e3a8a;
        }}
        .stat-label {{ color: #64748b; font-size: 0.875rem; }}
        .content {{ padding: 30px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{
            color: #1e3a8a;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }}
        .threat-card {{
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .threat-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .threat-title {{
            font-weight: bold;
            color: #1e293b;
        }}
        .severity {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .severity-critical {{ background: #fecaca; color: #991b1b; }}
        .severity-high {{ background: #fed7aa; color: #9a3412; }}
        .severity-medium {{ background: #fef3c7; color: #92400e; }}
        .severity-low {{ background: #dbeafe; color: #1e40af; }}
        .severity-info {{ background: #f3f4f6; color: #374151; }}
        .threat-description {{ color: #64748b; margin-bottom: 10px; }}
        .threat-meta {{
            display: flex;
            gap: 15px;
            font-size: 0.875rem;
            color: #94a3b8;
        }}
        .components {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .component-tag {{
            background: #e0e7ff;
            color: #3730a3;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.875rem;
        }}
        .footer {{
            background: #1e293b;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.875rem;
        }}
        .stride-matrix {{
            display: grid;
            grid-template-columns: 150px repeat(6, 1fr);
            gap: 10px;
            margin-top: 15px;
        }}
        .matrix-header {{
            background: #1e3a8a;
            color: white;
            padding: 10px;
            text-align: center;
            font-weight: bold;
            border-radius: 4px;
        }}
        .matrix-cell {{
            background: #f1f5f9;
            padding: 10px;
            text-align: center;
            border-radius: 4px;
        }}
        .matrix-cell.has-threat {{ background: #fecaca; }}
        .component-name {{
            background: #e2e8f0;
            padding: 10px;
            font-weight: bold;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Relatório de Modelagem de Ameaças</h1>
            <p>Análise STRIDE - Job #{job_id[:8]}</p>
            <p>Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        </div>

        <div class="summary">
            <div class="stat-card">
                <div class="stat-number">{len(architecture_graph.components)}</div>
                <div class="stat-label">Componentes</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(threats)}</div>
                <div class="stat-label">Ameaças</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #dc2626;">{len(critical)}</div>
                <div class="stat-label">Críticas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #ea580c;">{len(high)}</div>
                <div class="stat-label">Altas</div>
            </div>
        </div>

        <div class="content">
            <div class="section">
                <h2>📊 Matriz STRIDE</h2>
                <div class="stride-matrix">
                    <div class="component-name">Componente</div>
"""
        # Add STRIDE headers
        for cat, name in stride_categories.items():
            html += f'                    <div class="matrix-header" title="{name}">{cat}</div>\n'

        # Group threats by component
        component_threats: dict[str, set[str]] = {}
        for t in threats:
            if t.component_id not in component_threats:
                component_threats[t.component_id] = set()
            component_threats[t.component_id].add(t.category)

        # Add component rows
        for comp in architecture_graph.components[:10]:  # Limit to 10 for display
            comp_threats = component_threats.get(comp.id, set())
            html += f'                    <div class="component-name">{comp.type}</div>\n'
            for cat in stride_categories.keys():
                has_threat = 'has-threat' if cat in comp_threats else ''
                html += f'                    <div class="matrix-cell {has_threat}"></div>\n'

        html += """                </div>
            </div>

            <div class="section">
                <h2>🔴 Ameaças Críticas</h2>
"""

        # Critical threats
        if critical:
            for t in critical:
                html += self._threat_card(t, stride_categories)
        else:
            html += '<p style="color: #64748b;">Nenhuma ameaça crítica identificada.</p>'

        html += """
            </div>

            <div class="section">
                <h2>🟠 Ameaças de Alto Risco</h2>
"""

        # High threats
        if high:
            for t in high:
                html += self._threat_card(t, stride_categories)
        else:
            html += '<p style="color: #64748b;">Nenhuma ameaça de alto risco identificada.</p>'

        html += """
            </div>

            <div class="section">
                <h2>🔵 Demais Ameaças</h2>
"""

        # Medium, Low, Info threats
        for t in medium + low + info:
            html += self._threat_card(t, stride_categories)

        html += """
            </div>
        </div>

        <div class="footer">
            <p>FIAP STRIDE Threat Modeler © 2026 - Grupo 27</p>
            <p>Este é um relatório de teste gerado automaticamente.</p>
        </div>
    </div>
</body>
</html>
"""

        return html

    def _threat_card(self, threat: EnrichedThreat, categories: dict[str, str]) -> str:
        """Generate HTML for a threat card."""
        severity_class = threat.severity.value.lower()
        category_name = categories.get(threat.category, threat.category)

        cwe_info = f"<br><strong>CWE:</strong> {threat.cwe_id}" if threat.cwe_id else ""
        cve_info = f"<br><strong>CVEs:</strong> {', '.join(threat.cve_ids[:3])}" if threat.cve_ids else ""

        countermeasures_html = ""
        if threat.countermeasures:
            countermeasures_html = "<br><strong>Contramedidas:</strong><ul>"
            for cm in threat.countermeasures[:3]:
                countermeasures_html += f"<li>{cm.title}</li>"
            countermeasures_html += "</ul>"

        return f"""
                <div class="threat-card">
                    <div class="threat-header">
                        <span class="threat-title">[{threat.category}] {threat.category_name}</span>
                        <span class="severity severity-{severity_class}">{threat.severity.value.upper()}</span>
                    </div>
                    <div class="threat-description">{threat.description}</div>
                    <div class="threat-meta">
                        <span>🧩 {threat.component_type}</span>
                        <span>📁 {category_name}</span>
                    </div>
                    {cwe_info}
                    {cve_info}
                    {countermeasures_html}
                </div>
"""


# Singleton instance
report_generator = SimpleHTMLReportGenerator()
