# Divisão de Trabalho — Hackathon FIAP Fase 5

## 📋 Sumário

Este documento define como os 4 membros da equipe trabalham em paralelo nas 9 specs do projeto, respeitando as dependências do SDD e minimizando bloqueios.

---

## 🎯 Spec 000 — ✅ CONCLUÍDA

**Status**: ✅ **Implementada e mergeada em `main`**  
**Commit**: `20027e8` — feat: implementa Spec 000 — Contratos de Domínio

A [Spec 000 — Contratos de Domínio](../features/000-domain-contracts.md) foi **concluída** e está disponível em `main`. Todos os **models Pydantic** (`ArchitectureGraph`, `Threat`, `EnrichedThreat`, `Job`) estão implementados em `src/domain/models.py`.

> 🎉 **Time liberado para trabalhar em paralelo!** Use os mocks em `tests/mocks/` quando necessário.

| Modelo | Onde está definido | Usado por |
|--------|-------------------|-----------|
| `ArchitectureGraph` | `src/domain/models.py` | Spec 003 (produz) → Spec 004 (consome) |
| `Threat` | `src/domain/models.py` | Spec 004 (produz) → Spec 005/006 (consome) |
| `EnrichedThreat` | `src/domain/models.py` | Spec 005 (produz) → Spec 006 (consome) |
| `Job` | `src/domain/models.py` | Spec 001 (produz) → Spec 006 (consome) |

> ⚠️ **Regra de ouro**: ninguém altera esses models sem avisar no grupo. Mudanças exigem PR exclusiva.

---

## 👥 Membros e Atribuições

| Membro | GitHub | Spec(s) | Responsabilidade |
|--------|--------|---------|------------------|
| **Vagner Barbosa** | [@vagnerbarbosa](https://github.com/vagnerbarbosa) | **000** (Contratos) + **001** (API Core) + **003** (Detecção) | Contratos de domínio, scaffolding, integração CV→API |
| **Lucas Silva** | [@lucfsilva](https://github.com/lucfsilva) | **002** (Dataset/Treino) + **007** (CI/CD) | Dataset, treinamento YOLOv11n, pipeline de qualidade |
| **Adriel Santos** | [@AdrielCandido](https://github.com/AdrielCandido) | **004** (STRIDE) + **005** (Vulnerabilidades) | Motor STRIDE, busca CWE/CVE, contramedidas OWASP |
| **Leticia Nepomucena** | [@LeticiaNepomucena](https://github.com/LeticiaNepomucena) | **006** (Relatórios) + **009** (Vídeo) | Templates Jinja2, exportações, roteiro de apresentação |
| **Vagner Barbosa** | [@vagnerbarbosa](https://github.com/vagnerbarbosa) | **008** (Frontend React) | Interface web, upload, visualização de relatórios |

---

## 🔄 Ordem de Prioridade

### ✅ Fase 1 — Concluída
- [x] **Spec 000** — Contratos de Domínio implementados e mergeados

### 🚀 Fase 2 — Em Execução (trabalho em paralelo)
1. **Todos criam branches** `feature/00X-nome-da-spec` a partir da `main` atualizada
2. **Cada um implementa sua spec** usando **mocks/stubs** para as dependências ainda não prontas
3. **Pull Requests para `main`**, review cruzado, CI passando, merge

---

## 📦 Contratos de Domínio (Compartilhados)

Os seguintes models Pydantic são a "lingua franca" entre as specs:

| Modelo | Produzido por | Consumido por |
|--------|--------------|---------------|
| `ArchitectureGraph` | Spec 003 (Detecção) | Spec 004 (STRIDE) |
| `DetectedComponent` | Spec 003 (Detecção) | Spec 004 (STRIDE) |
| `Threat` | Spec 004 (STRIDE) | Spec 005 (Vuln) + Spec 006 (Report) |
| `EnrichedThreat` | Spec 005 (Vuln) | Spec 006 (Report) |
| `Job` | Spec 001 (API Core) | Spec 006 (Report) |

> **Regra de ouro**: ninguém altera esses models sem avisar no grupo. Se um campo precisar mudar, abre PR exclusiva para o contrato e todo mundo atualiza.

---

## 🧪 Como Trabalhar com Mocks/Stubs

Exemplo: Adriel (Spec 004) pode implementar o STRIDE antes do Lucas (Spec 003) terminar o modelo YOLOv11n:

```python
# tests/mocks/architecture_graph.py
from uuid import uuid4
from domain.models import ArchitectureGraph, DetectedComponent

mock_graph = ArchitectureGraph(
    components=[
        DetectedComponent(
            id=str(uuid4()),
            type="database",
            confidence=0.92,
            bbox=BoundingBox(x_min=100, y_min=100, x_max=200, y_max=200),
            center=Point(x_center=150, y_center=150),
        ),
    ],
    data_flows=[],
    trust_boundaries=[["database"]],
)
```

Cada spec deve incluir fixtures/mocks em `tests/mocks/` para os dados que consome.

---

## 🌿 Fluxo Git por Membro

```bash
# 1. Atualizar main
git checkout main
git pull origin main

# 2. Criar branch da sua spec
git checkout -b feature/004-stride-engine

# 3. Implementar (com mocks se necessário)
git add .
git commit -m "feat: implementa motor STRIDE com mapeamento YAML"

# 4. Push e PR
git push origin feature/004-stride-engine
# Abrir PR via GitHub (nunca mergear sozinho)
```

---

## 🚫 Anti-Padrões (O que NÃO fazer)

| ❌ Anti-Padrão | ✅ Correção |
|----------------|------------|
| "Vou esperar o Lucas terminar o modelo pra começar" | Use mocks. O contrato é a interface, não a implementação. |
| "Mudei `Threat` porque precisei de um campo a mais" | Abre PR só pro contrato. Avise no grupo. |
| "Commit direto na main" | **NUNCA.** Tudo passa por PR + review. |
| "Esqueci de rodar ruff/mypy antes do push" | Configure pre-commit hook (ver Spec 007). |
| "Dupliquei lógica porque não sabia que outro já fez" | Leia as specs vizinhas antes de codificar. |

---

## 📅 Checkpoint Diário (Opcional mas Recomendado)

**15 min no Discord/Slack/Grupo**:
1. O que fiz ontem?
2. O que vou fazer hoje?
3. Estou bloqueado em algo?

---

## 📊 Matriz de Dependências Visual

```
                    ┌─────────┐
                    │ Spec 000│
                    │(Contratos
                    │de Domínio)
                    └────┬────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         v               v               v
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  Vagner │────→│  Lucas  │     │ Adriel  │────→│ Leticia │
│  (001)  │     │  (002)  │     │ (004)   │     │ (006)   │
│  (003)  │←────│  (007)  │     │ (005)   │     │ (009)   │
└────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘
     │               │               │               │
     └───────────────┴───────────────┴───────────────┘
                    main (merge)
```

- Seta `────→` = produz dados que o outro consome
- Seta `←────` = depende de dados do outro (usa mock até pronto)

---

## 🚀 Guia de Implementação em Paralelo

> **✅ Spec 000 implementada! Todos podem começar AGORA.**

Este guia detalha como cada membro pode implementar suas specs usando **mocks** para desbloquear trabalho paralelo.

---

## 📊 Status de Paralelismo

| Membro | Spec | Status | Mock Necessário |
|--------|------|--------|-----------------|
| **Vagner** | 001 API Core | ✅ **Concluída** | `fake_job` |
| **Lucas** | 002 Dataset YOLO | ⏳ Em Progresso | Nenhum |
| **Vagner** | 003 Detecção | ✅ **Concluída** | `YOLOStub` |
| **Adriel** | 004 STRIDE | ⏳ Em Progresso | `fake_architecture_graph` |
| **Adriel** | 005 Vulnerabilidades | ⏳ Em Progresso | `fake_threats` |
| **Leticia** | 006 Relatórios | ⏳ Em Progresso | `fake_enriched`, `fake_job` |
| **Lucas** | 007 CI/CD | ⏳ Em Progresso | Todos os mocks |
| **Vagner** | 008 Frontend | ✅ **Concluída** | Layout completo, STRIDE, Grupo 27 |
| **Leticia** | 009 Vídeo | ⏳ Bloqueada | Aguardar integração |

---

## 🛠️ Padrão de Implementação

### Para cada spec:

1. **Crie sua branch**:
   ```bash
   git checkout -b feature/00X-nome-da-spec
   ```

2. **Use mocks quando necessário**:
   ```python
   from tests.mocks.fake_XXX import fake_XXX
   ```

3. **Teste com mocks primeiro**, depois substitua pela implementação real.

---

## 👤 Orientações por Membro

### Vagner — Spec 001 (API Core) + 003 (Detecção)

**Spec 001**: Implementar FastAPI + PostgreSQL usando `Job` dos contratos.

**Spec 003**: Implementar serviço de detecção usando stub YOLO:

```python
# tests/mocks/yolo_stub.py
class YOLOStub:
    def predict(self, image):
        return [
            {"class": "database", "confidence": 0.92, "bbox": [100, 100, 200, 200]},
            {"class": "api", "confidence": 0.88, "bbox": [300, 150, 400, 250]},
        ]
```

Quando Lucas (002) terminar, substitua `YOLOStub` pelo modelo real.

---

### Lucas — Spec 002 (Dataset YOLO) + 007 (CI/CD)

**Spec 002**: Trabalho independente de ML.
- Coletar/anotar imagens
- Treinar YOLOv11n → `models/best.pt`
- Exportar ONNX → `models/best.onnx`

**Spec 007**: Configurar GitHub Actions:
```yaml
jobs:
  test:
    steps:
      - run: ruff check src/
      - run: mypy src/
      - run: pytest --cov=src --cov-min=70
```

---

### Adriel — Spec 004 (STRIDE) + 005 (Vulnerabilidades)

**Spec 004**: Usar `fake_architecture_graph` para desenvolver motor STRIDE:

```python
from tests.mocks.fake_architecture_graph import fake_graph
from domain.models import ArchitectureGraph, Threat, Severity

class StrideEngine:
    def analyze(self, graph: ArchitectureGraph) -> list[Threat]:
        threats = []
        for component in graph.components:
            if component.type == "database":
                threats.append(Threat(
                    id=str(uuid4()),
                    category="I",  # Information Disclosure
                    component_id=component.id,
                    component_type=component.type,
                    description="Exfiltração de dados sensíveis",
                    severity=Severity.HIGH,
                ))
        return threats

# Testa com mock
engine = StrideEngine()
threats = engine.analyze(fake_graph)  # ✅ Funciona sem Spec 003
```

**Spec 005**: Usar `fake_threats` para desenvolver lookup de CWEs:

```python
from tests.mocks.fake_threats import fake_threats

class VulnerabilityService:
    def enrich(self, threat: Threat) -> EnrichedThreat:
        cwe = self._lookup_cwe(threat.category, threat.component_type)
        return EnrichedThreat(
            **threat.model_dump(),
            cwe_id=cwe.id,
            cwe_name=cwe.name,
            countermeasures=cwe.countermeasures,
        )

# Testa com mock
service = VulnerabilityService()
enriched = [service.enrich(t) for t in fake_threats]  # ✅ Funciona sem Spec 004
```

---

### Leticia — Spec 006 (Relatórios) + 009 (Vídeo)

**Spec 006**: Usar múltiplos mocks para desenvolver gerador de relatórios:

```python
from tests.mocks.fake_enriched_threats import fake_enriched
from tests.mocks.fake_job import fake_job
from jinja2 import Template

class ReportGenerator:
    def generate_md(self, threats, job) -> str:
        template = Template(open("templates/report.md.j2").read())
        return template.render(threats=threats, job=job)

# Testa com mocks
gen = ReportGenerator()
report = gen.generate_md(fake_enriched, fake_job)  # ✅ Funciona sem Specs 001/005
```

**Spec 009**: ⏳ **AGUARDAR**. Só comece quando todas as specs 001-008 estiverem integradas.

---

### Vagner — Spec 008 (Frontend React)

**Spec 008**: ✅ **IMPLEMENTADA**. Frontend React desenvolvido.

**Tecnologias Frontend:**
- **Framework**: React 18+ com TypeScript
- **Build Tool**: Vite 5.x
- **Styling**: Tailwind CSS 3.x
- **Fonte**: Inter (system-ui fallback)
- **Ícones**: Lucide React
- **State Management**: React Query
- **HTTP Client**: Axios
- **Container**: Nginx (multi-stage build)

**Cores:**
- Primária: `#10B981` (emerald)
- Secundária: `#3B82F6` (blue)
- Fundo escuro: `#0f172a` (slate-900)

**Funcionalidades Implementadas:**
- Layout responsivo com tema escuro
- Explicação da metodologia STRIDE (6 categorias)
- Seção "Sobre o Projeto" com integrantes do Grupo 27
- Links para perfis GitHub dos membros
- Link para repositório do projeto
- Copyright e nota de privacidade
- Dockerfile e nginx.conf configurados
- Integração com docker-compose.yml

**Portas:**
- Frontend: http://localhost:5173
- API: http://localhost:8001

```typescript
// Componentes principais
- App.tsx: Componente principal com navegação
- StrideCard: Cards explicativos das 6 categorias STRIDE
- AboutSection: Sobre o projeto, integrantes, tecnologias
- UploadZone: Área de upload (placeholder para integração futura)
- TechBadge: Badges de tecnologias utilizadas
```

---

## 📋 Checklist de Início

```markdown
### Vagner (001 + 003)
- [x] Branch `feature/001-api-core` criada ✅ **Implementada e mergeada**
- [x] Branch `feature/003-component-detection` criada ✅ **PR #11 aberta**
- [x] FastAPI + PostgreSQL configurados
- [x] `YOLOStub` funciona

### Lucas (002 + 007)
- [ ] Branch `feature/002-dataset-yolo` criada
- [ ] Branch `feature/007-ci-cd` criada
- [ ] Dataset coletado
- [ ] GitHub Actions configurado

### Adriel (004 + 005)
- [ ] Branch `feature/004-stride-engine` criada
- [ ] Branch `feature/005-vulnerability-lookup` criada
- [ ] `fake_graph` funciona
- [ ] `data/cwes.yaml` criado

### Leticia (006 + 009)
- [ ] Branch `feature/006-report-generator` criada
- [ ] Jinja2 instalado
- [ ] Templates iniciais criados
- [ ] Todos os mocks importam corretamente

### Vagner (008 Frontend)
- [x] Branch `feature/008-frontend-react` criada
- [x] Vite + React + TypeScript configurado
- [x] Tailwind CSS instalado
- [x] React Query configurado
- [x] Design system implementado
- [x] Explicação STRIDE implementada
- [x] Integrantes do Grupo 27 com links GitHub
- [x] Copyright e nota de privacidade
- [x] Dockerfile multi-stage configurado
- [x] Integrado ao docker-compose.yml
```

---

## 🔄 Ritmo de Trabalho

**Manhã** (5 min):
```bash
git checkout main && git pull origin main
git checkout feature/00X-sua-spec
git rebase main
```

**Durante o dia**:
- Implemente usando mocks
- Commite: `feat: ...`, `fix: ...`, `test: ...`

**Final do dia** (5 min):
```bash
git push origin feature/00X-sua-spec
```

---

## 🆘 Solução de Problemas

| Problema | Solução |
|----------|---------|
| Mock insuficiente | Estenda em `tests/mocks/` |
| Precisa alterar contrato | **AVISE O GRUPO** antes de tocar Spec 000 |
| Erro de import | `export PYTHONPATH=src` |
| Conflito de merge | Chame o time no Discord/Slack |

---

*Documento atualizado: 2026-07-11*
*Frontend React implementado*
