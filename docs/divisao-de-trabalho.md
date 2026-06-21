# Divisão de Trabalho — Hackathon FIAP Fase 5

## 📋 Sumário

Este documento define como os 4 membros da equipe trabalham em paralelo nas 8 specs do projeto, respeitando as dependências do SDD e minimizando bloqueios.

---

## 🎯 Spec 000 — O Ponto de Partida

**Antes de tudo**: a [Spec 000 — Contratos de Domínio](../features/000-domain-contracts.md) deve ser mergeada em `main`. Ela define os **models Pydantic** (`ArchitectureGraph`, `Threat`, `EnrichedThreat`, `Job`) que são a "lingua franca" entre todas as specs.

Sem a Spec 000, ninguém consegue trabalhar em paralelo. É o alicerce.

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
| **Leticia Nepomuceno** | [@LeticiaNepomucena](https://github.com/LeticiaNepomucena) | **006** (Relatórios) + **008** (Vídeo) | Templates Jinja2, exportações, roteiro de apresentação |

---

## 🔄 Ordem de Prioridade

1. **Primeiro (dia 0)**: Vagner mergeia a **[Spec 000](../features/000-domain-contracts.md)** em `main`. Sem os contratos de domínio, ninguém consegue trabalhar em paralelo.
2. **Segundo**: Todos criam branches `feature/00X-nome-da-spec` a partir da `main` atualizada.
3. **Terceiro**: Cada um implementa sua spec usando **mocks/stubs** para as dependências ainda não prontas.
4. **Quarto**: Pull Requests para `main`, review cruzado, CI passando, merge.

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
│  (003)  │←────│         │     │ (005)   │     │ (008)   │
└────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘
     │               │               │               │
     └───────────────┴───────────────┴───────────────┘
                    main (merge)
```

- Seta `────→` = produz dados que o outro consome
- Seta `←────` = depende de dados do outro (usa mock até pronto)

---

*Documento criado em: 2026-06-21*
*Atualizado conforme evolução das specs*
