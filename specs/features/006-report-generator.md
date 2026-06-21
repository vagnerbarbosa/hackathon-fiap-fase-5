# Spec: Gerador de Relatórios de Modelagem de Ameaças

---

## Contexto / Motuação

O hackathon exige um Relatório de Modelagem de Ameaças como entregável principal. Este relatório deve sintetizar todo o pipeline: componentes detectados, ameaças STRIDE, vulnerabilidades e contramedidas. A saída deve ser legível para arquitetos de software e equipes de segurança.

## Objetivo

Implementar um `ReportGenerator` que:
1. Receba o `EnrichedThreat` completo (Saída da Spec 005) + o `ArchitectureGraph` (Spec 003).
2. Gere um relatório estruturado em Markdown (legível) e JSON (processável).
3. Opcionalmente exporte para HTML (renderizado) ou PDF.
4. Ofereça um endpoint para download do relatório.

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

### RF-03: Relatório HTML (Opcional)
- Template Jinja2 renderizado para HTML com CSS básico.
- Responsivo (lê bem em mobile).
- Botão de "Exportar PDF" (via browser print ou WeasyPrint).

### RF-04: Score de Risco (Opcional)
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

### RF-05: Persistência do Relatório
- Relatório JSON salvo em arquivo (`reports/{job_id}.json`).
- Relatório Markdown salvo em arquivo (`reports/{job_id}.md`).
- Path armazenado no campo `output_report_path` do modelo `Job` (Spec 001).

## Requisitos Não-Funcionais (RNF)

### RNF-01: Performance
- Geração de relatório Markdown: < 1 segundo.
- Geração de relatório HTML: < 2 segundos.

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

### CA-03: Persistência
```gherkin
Dado que um relatório foi gerado
Então os arquivos .json e .md existem em reports/
E o campo Job.output_report_path está atualizado
```

## Dependências

### Internas
- **Spec 001** — depende de models (Job), storage, templates
- **Spec 003** — depende de ArchitectureGraph para seção 2
- **Spec 004** — depende de Threats para matriz STRIDE
- **Spec 005** — depende de EnrichedThreats para detalhamento

### Bibliotecas Python
- `jinja2==3.1.x`
- `markdown==3.6.x` (conversão MD -> HTML, opcional)
- `weasyprint==61.x` (geração de PDF, opcional — pode ser complexo de instalar)

## Decisões Técnicas (ADR)

### ADR-001: Markdown como formato primário
- **Contexto**: Precisamos de um formato legível, versionável, e fácil de gerar.
- **Decisão**: Markdown é o formato primário. HTML é secundário. PDF é opcional.
- **Justificativa**:
  - Markdown é universal (GitHub, GitLab, VS Code).
  - Não requer dependências pesadas.
  - Pode ser convertido para HTML/PDF por ferramentas externas se necessário.
- **Consequências**: Menos "bonito" que um PDF gerado, mas mais funcional para devs.

### ADR-002: Jinja2 para Templating
- **Contexto**: Precisamos de templates parametrizáveis para relatórios.
- **Decisão**: Jinja2 — padrão Python, simples, poderoso.
- **Justificativa**:
  - Integração natural com FastAPI/Pydantic.
  - Suporte a macros, filtros, herança de templates.
  - Templates versionados no git.
- **Consequências**: Templates podem ficar complexos. Separar em partials (`_header.md`, `_threat_table.md`, etc.).

## Módulos Planejados

| Arquivo | Responsabilidade |
|---------|------------------|
| `src/services/report_generator.py` | `ReportGenerator` — orquestração |
| `src/core/templates/stride_report.md.j2` | Template principal Markdown |
| `src/core/templates/stride_report.html.j2` | Template HTML (opcional) |
| `src/core/templates/partials/` | Partials reutilizáveis (matriz, sumário, etc.) |
| `src/api/routes/report.py` | Endpoints de download do relatório |
| `tests/unit/test_report_generator.py` | Testes de snapshot |

---

*Spec criada em: 2026-06-21*
