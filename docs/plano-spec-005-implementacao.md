# Plano de implementacao - Spec 005 Vulnerabilidades e Contramedidas

Responsavel: Adriel Santos (`@AdrielCandido`)
Projeto: Hackathon FIAP Fase 5 - Modelagem de Ameacas com IA (STRIDE)
Data deste plano: 2026-07-13
Objetivo: documentar a execucao da Spec 005 antes de qualquer alteracao de
codigo, seguindo o padrao usado na Spec 004.

Este plano foi preparado na branch `feature/005-vulnerability-service`, criada
a partir da `main`. Como o PR da Spec 004 ainda nao foi aprovado, a Spec 005
deve ser planejada com base nos contratos reais e mocks disponiveis na `main`,
sem depender de arquivos da branch `feature/004-stride-engine`.

Este arquivo e um documento de planejamento. Ele nao implementa codigo.

---

## 1. Estado atual observado

- A branch atual observada e `feature/005-vulnerability-service`.
- Esta branch foi criada a partir da `main`.
- A Spec 004 ainda nao deve ser assumida como aprovada ou disponivel nesta
  branch.
- Os contratos compartilhados existem em `src/domain/models.py`.
- O mock de entrada para a Spec 005 existe em
  `tests/mocks/fake_threats.py`.
- O mock de saida para a Spec 006 existe em
  `tests/mocks/fake_enriched_threats.py`.
- Ainda nao foram encontrados arquivos da implementacao da Spec 005.

Conclusao pratica: a Spec 005 pode ser preparada a partir da `main`, usando
`Threat`, `EnrichedThreat`, `Countermeasure` e os mocks existentes. A
implementacao deve aguardar aprovacao explicita.

---

## 2. Posicao da Spec 005 no pipeline

```text
Spec 004
StrideEngine
  |
  v
list[Threat]
  |
  v
Spec 005
VulnerabilityService
  |
  v
list[EnrichedThreat]
  |
  v
Spec 006
ReportGenerator
```

Entrega esperada quando autorizada:

1. Base local de vulnerabilidades e contramedidas.
2. Loader/consulta da base local.
3. Enriquecimento offline de ameacas.
4. NVD opcional com fallback seguro.
5. Testes unitarios sem internet e sem Redis real.

---

## 3. Contratos reais que devem ser respeitados

Fonte de verdade:

```text
src/domain/models.py
```

### Entrada

```python
list[Threat]
```

Campos reais de `Threat`:

```python
id: str
category: str
component_id: str
component_type: str
description: str
severity: Severity
affected_data_flows: list[str] = []
```

### Saida

```python
list[EnrichedThreat]
```

Campos reais de `EnrichedThreat`:

```python
id: str
category: str
component_id: str
component_type: str
description: str
severity: Severity
cwe_id: str | None = None
cwe_name: str | None = None
cve_ids: list[str] = []
countermeasures: list[Countermeasure] = []
```

Campos reais de `Countermeasure`:

```python
title: str
description: str
owasp_ref: str | None = None
```

Regra obrigatoria: nao alterar `src/domain/models.py` na Spec 005.

---

## 4. Divergencias da spec textual

A spec textual menciona modelos mais ricos:

- `Vulnerability`
- `EnrichedThreat.vulnerabilities`
- `Countermeasure.id`
- `Countermeasure.implementation`
- `Countermeasure.category`
- `Countermeasure.references`

Esses campos nao existem no contrato real. A implementacao deve adaptar:

| Informacao da spec textual | Destino no contrato real |
|----------------------------|--------------------------|
| CWE principal | `EnrichedThreat.cwe_id` |
| Nome da CWE | `EnrichedThreat.cwe_name` |
| CVEs encontrados | `EnrichedThreat.cve_ids` |
| Mitigacoes | `EnrichedThreat.countermeasures` |
| Detalhe pratico de implementacao | `Countermeasure.description` |
| Referencia OWASP/NIST | `Countermeasure.owasp_ref` |

Nao criar campos extras nos Pydantic models compartilhados.

---

## 5. Arquivos planejados

Criar somente apos aprovacao:

```text
config/vulnerability_db.yaml
src/core/vulnerability_db.py
src/services/countermeasure_lookup.py
src/services/cve_lookup.py
src/services/vulnerability_service.py
tests/unit/test_vulnerability_db.py
tests/unit/test_vulnerability_service.py
```

Nao criar PR antes de autorizacao explicita.

---

## 6. Base local de vulnerabilidades

Arquivo planejado:

```text
config/vulnerability_db.yaml
```

Formato:

```yaml
mappings:
  - component_type: "api"
    stride_category: "S"
    cwe_id: "CWE-287"
    cwe_name: "Improper Authentication"
    countermeasures:
      - title: "Implementar autenticacao forte"
        description: "Exigir MFA, tokens assinados e expiracao curta para endpoints sensiveis."
        owasp_ref: "OWASP Authentication Cheat Sheet"
```

Regras:

- YAML deve ser a fonte primaria.
- Deve funcionar offline.
- Deve ser versionavel e facil de revisar.
- Deve retornar um unico mapeamento principal por combinacao
  `component_type + stride_category` no MVP.
- Se houver duplicidade para a mesma combinacao, o loader deve falhar com erro
  claro ou manter comportamento deterministico documentado.

Cobertura inicial recomendada:

| Componente + STRIDE | CWE sugerida |
|---------------------|--------------|
| `api + S` | CWE-287 ou CWE-306 |
| `api + T` | CWE-472 |
| `api + I` | CWE-200 |
| `api + D` | CWE-400 |
| `api + E` | CWE-862 ou CWE-863 |
| `database + T` | CWE-89 ou CWE-943 |
| `database + I` | CWE-311 |
| `database + D` | CWE-400 |
| `web_server + D` | CWE-400 |
| `container + E` | CWE-250 |
| `queue + S` | CWE-345 |
| `cache + I` | CWE-200 |
| `storage + I` | CWE-200 ou CWE-311 |
| `storage + T` | CWE-345 ou CWE-494 |
| `data_flow + T` | CWE-345 |
| `data_flow + I` | CWE-319 |
| `data_flow + D` | CWE-400 |

Observacao: `data_flow` pode ser incluido como mapeamento preventivo caso a
implementacao aprovada da Spec 004 represente ameacas de fluxo com
`component_type="data_flow"`. Se a Spec 004 aprovada escolher outro formato,
ajustar este mapeamento antes da implementacao.

---

## 7. Loader da base local

Arquivo planejado:

```text
src/core/vulnerability_db.py
```

Responsabilidades:

- carregar YAML;
- validar que `mappings` e uma lista;
- validar categorias STRIDE (`S`, `T`, `R`, `I`, `D`, `E`);
- validar contramedidas com `title`, `description` e `owasp_ref` opcional;
- consultar por `component_type` e `stride_category`;
- retornar `None` quando nao houver mapeamento;
- nunca acessar internet.

Interface sugerida:

```python
class VulnerabilityDatabase:
    @classmethod
    def from_file(cls, path: Path) -> "VulnerabilityDatabase":
        ...

    def find(
        self,
        component_type: str,
        stride_category: str,
    ) -> VulnerabilityMapping | None:
        ...
```

`VulnerabilityMapping` deve ser interno ao modulo, como dataclass ou Pydantic
model nao compartilhado.

---

## 8. Lookup de contramedidas

Arquivo planejado:

```text
src/services/countermeasure_lookup.py
```

Responsabilidades:

- converter contramedidas do YAML para `Countermeasure`;
- fornecer fallback por categoria STRIDE;
- nao exigir campos que nao existem no contrato real.

Fallback recomendado:

| STRIDE | Contramedidas |
|--------|---------------|
| `S` | MFA, tokens assinados, mTLS |
| `T` | TLS 1.3, HMAC/assinatura, integridade |
| `R` | logs imutaveis, auditoria centralizada |
| `I` | criptografia em transito, criptografia em repouso, mascaramento |
| `D` | rate limiting, circuit breaker, WAF/autoscaling |
| `E` | RBAC, least privilege, isolamento/sandboxing |

---

## 9. Lookup de CVEs

Arquivo planejado:

```text
src/services/cve_lookup.py
```

NVD deve ser opcional.

Comportamento:

- se `NVD_API_KEY` nao existir, nao chamar NVD;
- aceitar client HTTP injetavel para testes;
- usar timeout curto;
- em erro HTTP, timeout ou parse invalido, retornar `[]`;
- limitar a quantidade de CVEs retornadas para evitar relatorio ruidoso;
- nao depender de internet em testes unitarios.

Interface sugerida:

```python
class CveLookupClient:
    async def search(
        self,
        cwe_id: str | None,
        keyword: str | None = None,
    ) -> list[str]:
        ...
```

---

## 10. VulnerabilityService

Arquivo planejado:

```text
src/services/vulnerability_service.py
```

Interface publica:

```python
class VulnerabilityService:
    async def enrich(self, threats: list[Threat]) -> list[EnrichedThreat]:
        ...
```

Fluxo:

```text
enrich(threats)
  se threats estiver vazio, retornar []
  carregar base local
  para cada threat:
      mapping = db.find(threat.component_type, threat.category)
      countermeasures = especificas do mapping ou fallback da categoria
      cve_ids = await cve_lookup.search(mapping.cwe_id, keyword) se aplicavel
      montar EnrichedThreat preservando campos originais
  retornar lista na mesma ordem
```

O servico deve aceitar dependencias injetaveis para facilitar testes:

- `database`
- `countermeasure_lookup`
- `cve_lookup`
- cache opcional

---

## 11. Cache

A spec textual pede Redis, mas a implementacao nao deve bloquear se a
infraestrutura ainda nao existir.

Abordagem planejada:

- se houver wrapper de cache da Spec 001, usar por injecao;
- se nao houver, usar cache em memoria simples ou nao usar cache na primeira
  entrega;
- nunca exigir Redis real nos testes unitarios;
- documentar a integracao futura.

Chave:

```text
vuln:{component_type}:{stride_category}
```

TTL:

```text
86400 segundos
```

---

## 12. Testes obrigatorios

Criar apos aprovacao:

- `api + S` retorna CWE de autenticacao e contramedida.
- `database + I` retorna CWE e contramedidas de criptografia/mascaramento.
- `data_flow + I` retorna mapeamento ou fallback coerente.
- Threat sem mapeamento retorna `EnrichedThreat` valido.
- Campos originais da `Threat` sao preservados.
- Lista vazia retorna lista vazia.
- Sem `NVD_API_KEY`, NVD nao e chamada.
- NVD indisponivel nao quebra o enriquecimento.
- Loader falha com erro claro para YAML invalido.
- Resultado preserva a ordem de entrada.

Comandos esperados:

```powershell
$env:PYTHONPATH = "src"
python -m pytest tests\unit\test_vulnerability_db.py tests\unit\test_vulnerability_service.py
```

Se disponivel:

```powershell
ruff check .
mypy src
```

---

## 13. Checklist antes de implementar

- [ ] Voce aprovou explicitamente a implementacao.
- [ ] Branch correta definida para a Spec 005.
- [ ] Confirmado se a branch deve partir da `main` ou da branch da Spec 004.
- [ ] `src/domain/models.py` lido e mantido intacto.
- [ ] Mocks de `Threat` suficientes enquanto a Spec 004 nao estiver aprovada na
  `main`.
- [ ] Decidido se NVD sera stub seguro ou client opcional completo.
- [ ] Decidido se cache sera memoria/injetavel ou wrapper existente.

---

## 14. Checklist de entrega da Spec 005

- [ ] `config/vulnerability_db.yaml` criado.
- [ ] `src/core/vulnerability_db.py` criado.
- [ ] `src/services/countermeasure_lookup.py` criado.
- [ ] `src/services/cve_lookup.py` criado.
- [ ] `src/services/vulnerability_service.py` criado.
- [ ] `VulnerabilityService.enrich` e async.
- [ ] Entrada e `list[Threat]`.
- [ ] Saida e `list[EnrichedThreat]`.
- [ ] Base local funciona offline.
- [ ] NVD e opcional.
- [ ] Falha da NVD nao quebra o fluxo.
- [ ] Redis nao e obrigatorio.
- [ ] Threat sem mapeamento continua valida.
- [ ] Campos originais da `Threat` sao preservados.
- [ ] Testes unitarios principais passam.
- [ ] `src/domain/models.py` nao foi alterado.

---

## 15. Template de PR futuro

Nao abrir PR antes de autorizacao explicita.

Titulo sugerido:

```text
feat: implementa servico de vulnerabilidades e contramedidas
```

Descricao sugerida:

```markdown
## Resumo
- Implementa VulnerabilityService para enriquecer Threats.
- Adiciona base YAML offline com CWE e contramedidas.
- Adiciona fallback de contramedidas por categoria STRIDE.
- Adiciona client NVD opcional com fallback seguro.
- Adiciona testes unitarios para enriquecimento offline.

## Contratos
- Usa Threat, EnrichedThreat e Countermeasure de src/domain/models.py.
- Nao altera contratos compartilhados.

## Validacoes
- [ ] python -m pytest tests/unit/test_vulnerability_db.py tests/unit/test_vulnerability_service.py
- [ ] python -m pytest
- [ ] ruff check .
- [ ] mypy src

## Observacoes
- Base local e fonte primaria.
- NVD e Redis sao opcionais e possuem fallback.
- Testes unitarios nao dependem de internet.
```

---

## 16. Prompt para a proxima etapa autorizada

Quando quiser autorizar a implementacao, use algo como:

```text
Autorizo implementar a Spec 005 seguindo docs/spec-005-vulnerability-service.md
e docs/plano-spec-005-implementacao.md.
Nao abra PR ainda.
```

Para PR, use uma autorizacao separada:

```text
Autorizo preparar/abrir o PR da Spec 005.
```
