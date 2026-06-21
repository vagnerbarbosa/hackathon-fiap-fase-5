# Spec: Motor de Modelagem de Ameaças STRIDE

---

## Contexto / Motivação

Após a detecção de componentes de arquitetura (Spec 003), o sistema precisa aplicar a metodologia STRIDE para identificar ameaças de segurança em cada componente e fluxo de dados. Esta spec isola o motor de análise STRIDE, transformando uma lista de componentes detectados em uma matriz completa de ameaças.

## Objetivo

Implementar um `StrideEngine` que:
1. Receba uma `ArchitectureGraph` (componentes + fluxos de dados + trust boundaries) da Spec 003.
2. Aplique sistematicamente as 6 categorias STRIDE para cada elemento da arquitetura.
3. Gere uma lista estruturada de ameaças, priorizadas por criticidade.
4. Cada ameaça deve conter: descrição, categoria STRIDE, componente afetado, justificativa.

## Requisitos Funcionais (RF)

### RF-01: Taxonomia de Ameaças STRIDE por Componente

Para cada tipo de componente, mapear ameaças padrão da metodologia STRIDE:

| Componente | S | T | R | I | D | E |
|------------|---|---|---|---|---|---|
| **user** | S: Spoofing de identidade | — | R: Negar ações realizadas | — | — | — |
| **web_server** | S: Falso servidor | T: Alterar respostas | R: Negar logs | I: Leak de headers | D: DDoS | E: Escalar para shell |
| **api** | S: Spoofing de tokens | T: Tamper requests/responses | R: Negar chamadas | I: Expor dados sensíveis | D: Rate exhaustion | E: Bypass authZ |
| **database** | — | T: Alterar registros | R: Negar transações | I: Exfiltração de dados | D: FLOOD queries | E: Privilege escalation |
| **queue** | S: Spoofing de mensagens | T: Alterar payload | R: Negar envio | I: Espionar fila | D: Encher fila | E: Acesso não autorizado |
| **cache** | — | T: Poisoning de cache | — | I: Leak de dados em cache | D: Cache busting | — |
| **external_service** | S: DNS spoofing / MITM | T: Alterar callbacks | R: Negar integração | I: Leak via third-party | D: Indisponibilidade do parceiro | E: — |
| **mobile_app** | S: Clonagem de app | T: Tamper APK/IPA | R: Negar uso local | I: Leak de storage local | D: Crash loops | E: Jailbreak/root bypass |
| **container** | S: Image spoofing | T: Alterar imagem | — | I: Secret leak em env | D: Resource exhaustion | E: Container escape |
| **storage** | — | T: Alterar arquivos | R: Negar upload | I: Acesso não autorizado | D: Fill storage | E: ACL bypass |

**Data Flows (entre componentes)**:
- **Tampering**: interceptação e modificação de dados em trânsito.
- **Information Disclosure**: sniffing de dados em trânsito (Man-in-the-Middle).
- **Denial of Service**: flood no canal de comunicação.

**Trust Boundaries**:
- Todo cruzamento de trust boundary deve ser analisado contra **todas** as 6 categorias STRIDE.

### RF-02: Motor STRIDE (`StrideEngine`)
```python
class Threat(BaseModel):
    id: str
    category: str           # "S" | "T" | "R" | "I" | "D" | "E"
    category_name: str      # "Spoofing" | "Tampering" | ...
    component_id: str
    component_type: str
    description: str
    justification: str      # Por que esta ameaça se aplica a este componente
    severity: str           # "critical" | "high" | "medium" | "low"
    affected_data_flows: list[str] | None  # IDs dos fluxos afetados

class StrideEngine:
    async def analyze(self, graph: ArchitectureGraph) -> list[Threat]:
        """
        Para cada componente e fluxo, aplica STRIDE.
        Retorna lista de Threats priorizada.
        """
        ...
```

### RF-03: Priorização de Severidade
O motor deve atribuir severidade com base em regras:
- **Critical**: Data Store (DB, Storage) + Information Disclosure ou Tampering.
- **High**: API + Elevation of Privilege; Trust Boundary + qualquer STRIDE.
- **Medium**: Web Server + DoS; Queue + Spoofing.
- **Low**: Componentes internos com baixo impacto (Cache + DoS leve).

Regras podem ser ajustadas, mas devem ser documentadas e reproduzíveis.

### RF-04: Extensibilidade
O mapeamento componente → ameaças deve ser configurável via arquivo YAML/JSON:
```yaml
# stride_mappings.yaml
components:
  api:
    threats:
      - category: "S"
        description: "Attacker forges JWT tokens to impersonate users"
        justification: "APIs rely on tokens; weak signing allows spoofing"
      - category: "T"
        description: "Request/response payloads modified in transit"
        justification: "Without TLS, data flows are susceptible to tampering"
```
- O motor carrega este arquivo na inicialização.
- Permite adicionar novos componentes ou ameaças sem alterar código.

### RF-05: Validação Cruzada
Se um Data Flow conecta dois componentes, o motor deve considerar ameaças que afetam **ambos** os componentes e o fluxo em si. Exemplo: `user → api`:
- User: Spoofing (S)
- API: Spoofing (S), Tampering (T), Information Disclosure (I), Elevation (E)
- Data Flow: Tampering (T), Information Disclosure (I), DoS (D)

## Requisitos Não-Funcionais (RNF)

### RNF-01: Performance
- Análise STRIDE de uma arquitetura com 10 componentes: < 500ms.
- O motor é puramente computacional (sem chamadas externas nesta spec).

### RNF-02: Determinismo
- Para o mesmo `ArchitectureGraph`, o motor deve sempre produzir a mesma lista de ameaças (ordem por severidade, depois por categoria).

### RNF-03: Testabilidade
- Testes unitários com grafos fictícios (mock).
- Testes de snapshot para garantir que o output não muda indevidamente.

## Critérios de Aceitação

### CA-01: Ameaças por Componente
```gherkin
Dado uma ArchitectureGraph com um componente "database"
Quando o StrideEngine.analyze() é executado
Então retorna ameaças nas categorias T, R, I, D, E para "database"
E não retorna ameaças S (Spoofing) para "database"
```

### CA-02: Ameaças em Trust Boundaries
```gherkin
Dado um Data Flow que cruza um trust boundary (ex: user → api)
Quando o motor analisa
Então retorna ameaças T, I, D para o Data Flow
E marca affected_data_flows com o ID do fluxo
```

### CA-03: Priorização
```gherkin
Dado uma ameaça de Information Disclosure em um database
E uma ameaça de DoS em um cache
Quando a lista é ordenada por severidade
Então a ameaça do database aparece antes (critical > low)
```

### CA-04: Extensibilidade
```gherkin
Dado um arquivo stride_mappings.yaml com um novo componente "blockchain_node"
Quando o motor é reiniciado
Então reconhece o novo componente e aplica as ameaças configuradas
```

## Contratos de Entrada/Saída

### Entrada (consumido desta spec)
| Contrato | Tipo | Vem de |
|----------|------|--------|
| `ArchitectureGraph` | Pydantic model | Spec 003 (Detecção) |
| `DetectedComponent` | Pydantic model | Spec 003 (Detecção) |
| `DataFlow` | Pydantic model | Spec 003 (Detecção) |

### Saída (produzido por esta spec)
| Contrato | Tipo | Vai para |
|----------|------|----------|
| `Threat` | Pydantic model | Spec 005 (Vulnerabilidades) + Spec 006 (Relatórios) |

### Mock para Spec 005 (quando motor STRIDE ainda não está pronto)

```python
# tests/mocks/fake_threats.py
from uuid import uuid4
from domain.models import Threat, Severity

fake_threats = [
    Threat(
        id=str(uuid4()),
        category="T",  # Tampering
        component_id="comp-db-1",
        component_type="database",
        description="Possibilidade de alteração não autorizada dos dados em repouso.",
        severity=Severity.HIGH,
        affected_data_flows=[],
    ),
    Threat(
        id=str(uuid4()),
        category="I",  # Information Disclosure
        component_id="comp-db-1",
        component_type="database",
        description="Exfiltração de dados sensíveis sem criptografia.",
        severity=Severity.CRITICAL,
        affected_data_flows=[],
    ),
]
```

## Dependências

### Internas
- **Spec 001** — depende da estrutura `src/services/`, logging
- **Spec 003** — consome `ArchitectureGraph` como input

### Bibliotecas Python
- `pyyaml==6.0.x` (carregamento do mapeamento)
- `pytest==8.x` (testes)

## Decisões Técnicas (ADR)

### ADR-001: Mapeamento YAML vs. Banco de Dados
- **Contexto**: Ameaças STRIDE são relativamente estáveis, mas precisam ser extensíveis.
- **Decisão**: Arquivo YAML versionado no repositório (`config/stride_mappings.yaml`).
- **Justificativa**:
  - YAML é legível, difável, e não requer migração de banco.
  - Mudanças no mapeamento acompanham o código (infra-as-code para regras).
  - Se escalar para 1000+ regras, migra para DB no futuro.
- **Consequências**: Hot-reload requer reiniciar o serviço. Aceitável para MVP.

### ADR-002: Motor Puro Python (sem LLM)
- **Contexto**: Poderíamos usar um LLM para gerar ameaças STRIDE dinamicamente.
- **Decisão**: Motor baseado em regras estruturadas (YAML), sem chamada a LLM.
- **Justificativa**:
  - STRIDE é uma metodologia madura com mapeamentos bem definidos por componente.
  - Regras são determinísticas, rápidas, e não dependem de serviço externo.
  - LLM pode ser usado futuramente para enriquecer descrições, mas não como motor principal.
- **Consequências**: Menos "inteligente" para casos edge, mas mais confiável e rápido.

## Módulos Planejados

| Arquivo | Responsabilidade |
|---------|------------------|
| `src/services/stride_engine.py` | `StrideEngine` — orquestração da análise |
| `src/core/stride_mappings.py` | Carregamento e validação do YAML de mapeamentos |
| `src/core/stride_rules.py` | Regras de severidade e priorização |
| `config/stride_mappings.yaml` | Mapeamento componente → ameaças STRIDE |
| `tests/unit/test_stride_engine.py` | Testes com grafos fictícios |
| `tests/unit/test_stride_mappings.py` | Testes de carregamento YAML |

---

*Spec criada em: 2026-06-21*
