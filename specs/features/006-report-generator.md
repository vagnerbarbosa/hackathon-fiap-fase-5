# Spec: Gerador de Relatórios de Modelagem de Ameaças

---

## Contexto / Motuação

O hackathon exige um Relatório de Modelagem de Ameaças como entregável principal. Este relatório deve sintetizar todo o pipeline: componentes detectados, ameaças STRIDE, vulnerabilidades e contramedidas. A saída deve ser legível para arquitetos de software e equipes de segurança.

### Status Atual (MVP)

**⚠️ Implementação Parcial**: O arquivo `src/services/simple_report.py` contém uma versão **MVP (temporária)** do gerador de relatórios. Esta implementação:
- Gera HTML básico a partir de dados mock/enriquecidos
- Serve para validar o fluxo end-to-end enquanto a Spec 006 completa não é implementada
- **Será substituída** pela implementação completa conforme os requisitos abaixo

A versão final deve seguir todos os RFs (Requisitos Funcionais) documentados nesta spec, incluindo suporte a múltiplos formatos (Markdown, JSON, HTML, CSV, PDF) via templates Jinja2.

## Objetivo

Implementar um `ReportGenerator` que:
1. Receba o `EnrichedThreat` completo (Saída da Spec 005) + o `ArchitectureGraph` (Spec 003).
2. Gere um relatório estruturado em Markdown (legível) e JSON (processável).
3. Opcionalmente exporte para HTML (renderizado) ou PDF.
4. Ofereça um endpoint para download do relatório.

### Roadmap de Implementação

| Fase | Arquivo | Descrição | Status |
|------|---------|-------------|--------|
| **MVP** | `src/services/simple_report.py` | Versão simples, HTML básico, dados mock | ✅ Implementado |
| **Completa** | `src/services/report_generator.py` | Versão completa com todos os formatos | ⏳ Pendente |

**Nota**: O `simple_report.py` será **substituído** quando a implementação completa da Spec 006 for desenvolvida. A API deve manter compatibilidade backward (mesmos endpoints, mesma resposta JSON).

## Requisitos Funcionais (RF)

### RF-01: Relatório Markdown
Template Jinja2 (`templates/stride_report.md.j2`) gerando seções:

```markdown
# Relatório de Modelagem de Ameaças — STRIDE

## 1. Resumo Executivo
- Data da análise: {{ timestamp }}
- Imagem analisada: {{ image_name }}
- Componentes detectados: {{ component_count }}
- Ameaças identificadas: {{ threat_count }}
- Ameaças críticas: {{ critical_count }}

## 2. Diagrama de Arquitetura Analisado
- Descrição textual dos componentes
- Lista de fluxos de dados

## 3. Matriz STRIDE
| Componente | S | T | R | I | D | E |
|------------|---|---|---|---|---|---|
| user       | ✓ |   | ✓ |   |   |   |
| api        | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| database   |   | ✓ | ✓ | ✓ | ✓ | ✓ |

## 4. Detalhamento de Ameaças

### 4.1 Ameaças Críticas
{{#each critical_threats}}
#### {{ category }} — {{ component_type }}
- **Descrição**: {{ description }}
- **Justificativa**: {{ justification }}
- **Severidade**: {{ severity }}
- **Vulnerabilidades**: {{#each vulnerabilities}} {{ cwe_id }} — {{ title }} {{/each}}
- **Contramedidas**:
  {{#each countermeasures}}
  - **{{ title }}**: {{ description }}
    - *Implementação*: {{ implementation }}
    - *Referência*: {{ references }}
  {{/each}}
{{/each}}

### 4.2 Ameaças de Alto Risco
...

### 4.3 Ameaças de Médio/Baixo Risco
...

## 5. Sumário de Contramedidas Recomendadas
Tabela consolidada de todas as contramedidas por prioridade.

## 6. Recomendações
- Top 3 ações prioritárias
- Próximos passos para hardening
```

### RF-02: Relatório JSON (API)
Endpoint `GET /api/v1/threat-model/{job_id}/report?format=json` retorna:
```json
{
  "job_id": "uuid",
  "timestamp": "2026-06-21T14:00:00Z",
  "image_name": "arquitetura1.png",
  "components": [...],
  "data_flows": [...],
  "trust_boundaries": [...],
  "threats": [
    {
      "id": "...",
      "category": "I",
      "component_type": "database",
      "severity": "critical",
      "description": "...",
      "vulnerabilities": [...],
      "countermeasures": [...]
    }
  ],
  "summary": {
    "total_threats": 25,
    "critical": 3,
    "high": 8,
    "medium": 10,
    "low": 4
  }
}
```

### RF-03: Relatório HTML (Exportação)
- Template Jinja2 renderizado para HTML com CSS básico.
- Responsivo (lê bem em mobile).
- Cores de severidade (vermelho=critical, laranja=high, amarelo=medium, verde=low).

### RF-04: Relatório CSV (Exportação)
- Endpoint `GET /api/v1/threat-model/{job_id}/report?format=csv` retorna CSV flat.
- Colunas: `threat_id`, `category`, `component_type`, `severity`, `description`, `cwe_id`, `countermeasure_title`.
- Útil para importar em planilhas (Excel, Google Sheets) ou SIEM.
- Gerado com `pandas.DataFrame.to_csv()`.

### RF-05: Relatório PDF (Exportação)
- Endpoint `GET /api/v1/threat-model/{job_id}/report?format=pdf` retorna PDF.
- Renderizado via **WeasyPrint** a partir do template HTML + CSS.
- Inclui header com logo/nome do projeto e footer com número de página.
- Ideal para compartilhamento executivo e entregáveis formais.
- Fallback: se WeasyPrint falhar (fonts ausentes), retornar HTML com instrução "imprimir como PDF".

### RF-06: Score de Risco
Implementar cálculo de score agregado por componente:
```
risk_score(component) = Σ(severity_weight[threat.severity])

severity_weight = {
    "critical": 10,
    "high": 7,
    "medium": 4,
    "low": 1
}
```
- Componentes com maior score são destacados no relatório.

### RF-07: Endpoint Único de Relatório
`GET /api/v1/threat-model/{job_id}/report?format={md|json|html|csv|pdf}`
- `json` → resposta inline (Content-Type: application/json).
- `md|html|csv|pdf` → download como attachment (Content-Disposition: attachment).
- Formato default: `json`.

### RF-08: Persistência dos Relatórios
- Todos os formatos gerados são salvos em `reports/{job_id}.{ext}`:
  - `.json` — estrutura completa da análise
  - `.md` — relatório legível
  - `.html` — versão renderizada
  - `.csv` — dados tabulares
  - `.pdf` — versão executiva
- Path armazenado no campo `output_report_path` do modelo `Job` (Spec 001) como lista de arquivos.

## Requisitos Não-Funcionais (RNF)

### RNF-01: Performance
- Geração Markdown/JSON: < 500ms.
- Geração HTML: < 1 segundo.
- Geração CSV: < 500ms.
- Geração PDF (WeasyPrint): < 5 segundos.

### RNF-02: Estética
- Markdown deve ser renderizável corretamente no GitHub/GitLab.
- HTML deve ter identidade visual básica (logo FIAP, cores de severidade).

### RNF-03: Testabilidade
- Testes de snapshot para templates Jinja2 (comparar output esperado).
- Fixtures com dados fictícios de ameaças enriquecidas.

## Critérios de Aceitação

### CA-01: Relatório Markdown Completo
```gherkin
Dado um Job concluído com ameaças enriquecidas
Quando o usuário acessa GET /api/v1/threat-model/{id}/report?format=md
Então recebe um arquivo Markdown com todas as seções obrigatórias
E a matriz STRIDE está preenchida corretamente
E as ameaças estão agrupadas por severidade
```

### CA-02: Relatório JSON Estruturado
```gherkin
Dado o mesmo Job concluído
Quando acessa GET /api/v1/threat-model/{id}/report?format=json
Então recebe JSON válido com todos os campos documentados
E o campo summary.total_threats condiz com o tamanho da lista
```

### CA-03: Relatório CSV
```gherkin
Dado um Job concluído
Quando acessa GET /api/v1/threat-model/{id}/report?format=csv
Então recebe um arquivo CSV com colunas: threat_id, category, component_type, severity, description, cwe_id, countermeasure_title
E o Content-Type é text/csv
```

### CA-04: Relatório PDF
```gherkin
Dado um Job concluído
Quando acessa GET /api/v1/threat-model/{id}/report?format=pdf
Então recebe um arquivo PDF binário
E o PDF contém header com nome do projeto e footer com número de página
E o Content-Type é application/pdf
```

### CA-05: Persistência
```gherkin
Dado que um relatório foi gerado
Então os arquivos .json, .md, .html, .csv e .pdf existem em reports/
E o campo Job.output_report_path contém a lista de todos os arquivos gerados
```

## Contratos de Entrada/Saída

### Entrada (consumido desta spec)
| Contrato | Tipo | Vem de |
|----------|------|--------|
| `EnrichedThreat` | `list[EnrichedThreat]` | Spec 005 (Vulnerabilidades) |
| `ArchitectureGraph` | Pydantic model | Spec 003 (Detecção) — opcional, para diagrama no relatório |
| `Job` | Pydantic model | Spec 001 (API Core) — para metadados do job |

### Saída (produzido por esta spec)
| Artefato | Formato | Destino |
|----------|---------|---------|
| Relatório | `.md`, `.json`, `.html`, `.csv`, `.pdf` | Download do usuário / storage local |

### Mock para desenvolvimento independente

```python
# tests/mocks/fake_report_input.py
from uuid import uuid4
from domain.models import (
    EnrichedThreat, Severity, Countermeasure,
    ArchitectureGraph, DetectedComponent, Job, JobStatus
)

fake_job = Job(
    id=uuid4(),
    status=JobStatus.COMPLETED,
    input_image_path="/uploads/diagrama.png",
    output_report_path="/reports/job-123/report.md",
)
```

## Dependências

### Pré-requisito
- **Spec 000** — consome os contratos de domínio (\`ArchitectureGraph\`, \`Threat\`, \`EnrichedThreat\`, \`Job\`) definidos em \`src/domain/models.py\`.

### Pré-requisito
- **Spec 000** — esta spec consome os contratos de domínio (`ArchitectureGraph`, `Threat`, `EnrichedThreat`, `Job`) definidos em `src/domain/models.py`.


### Internas
- **Spec 001** — depende de models (Job), storage, templates
- **Spec 003** — depende de ArchitectureGraph para seção 2
- **Spec 004** — depende de Threats para matriz STRIDE
- **Spec 005** — depende de EnrichedThreats para detalhamento

### Bibliotecas Python
- `jinja2==3.1.x` — templating Markdown/HTML
- `markdown==3.6.x` — conversão MD → HTML (opcional)
- `pandas==2.2.x` — geração de CSV via `DataFrame.to_csv()`
- `weasyprint==61.x` — geração de PDF a partir de HTML+CSS (render engine visual)

## Decisões Técnicas (ADR)

### ADR-001: Múltiplos formatos de saída
- **Contexto**: Diferentes stakeholders precisam consumir o relatório de formas distintas: devs (Markdown), máquinas (JSON), executivos (PDF), analistas (CSV).
- **Decisão**: Suportar 5 formatos: JSON (API default), Markdown (legível), HTML (renderizado), CSV (dados tabulares), PDF (executivo formal).
- **Justificativa**:
  - JSON: formato nativo da API, processável por outras ferramentas.
  - Markdown: universal, versionável, leve.
  - HTML: renderizado com CSS para apresentações.
  - CSV: importável em Excel/SIEM para análise quantitativa.
  - PDF: gerado via WeasyPrint a partir do HTML, ideal para entregáveis formais.
- **Consequências**: Mais templates para manter, mas cobertura completa de casos de uso.

### ADR-002: Jinja2 para Templating
- **Contexto**: Precisamos de templates parametrizáveis para relatórios.
- **Decisão**: Jinja2 — padrão Python, simples, poderoso.
- **Justificativa**:
  - Integração natural com FastAPI/Pydantic.
  - Suporte a macros, filtros, herança de templates.
  - Templates versionados no git.
- **Consequências**: Templates podem ficar complexos. Separar em partials (`_header.md`, `_threat_table.md`, etc.).

## Módulos Planejados

| Arquivo | Responsabilidade | Status |
|---------|------------------|--------|
| `src/services/simple_report.py` | **TEMPORÁRIO/MVP**: HTML básico para validação do fluxo | ✅ Implementado (será removido) |
| `src/services/report_generator.py` | `ReportGenerator` — orquestração de todos os formatos | ⏳ Pendente |
| `src/services/csv_exporter.py` | Exportação de ameaças para CSV via pandas | ⏳ Pendente |
| `src/services/pdf_exporter.py` | Renderização HTML → PDF via WeasyPrint | ⏳ Pendente |
| `src/core/templates/stride_report.md.j2` | Template Markdown | ⏳ Pendente |
| `src/core/templates/stride_report.html.j2` | Template HTML (base para PDF) | ⏳ Pendente |
| `src/core/templates/stride_report.csv.j2` | Template CSV (header/row) | ⏳ Pendente |
| `src/core/templates/partials/` | Partials reutilizáveis | ⏳ Pendente |
| `src/api/routes/report.py` | Endpoint único `GET /report?format=` | 🔄 Parcial (usa simple_report) |
| `tests/unit/test_report_generator.py` | Testes de snapshot para todos os formatos | ⏳ Pendente |

### Nota sobre simple_report.py

O arquivo `simple_report.py` atual:
- É uma **implementação temporária** para permitir testes end-to-end
- Gera HTML básico sem templates Jinja2
- Não suporta exportação para Markdown, CSV ou PDF
- Deve ser **removido/substituído** pela implementação completa da Spec 006
- Mantém compatibilidade de interface (mesmos inputs/outputs)

---

*Spec criada em: 2026-06-21*
