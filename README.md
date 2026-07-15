# 🛡️🔍 Hackathon FIAP Fase 5 - Modelagem de Ameaças com IA (STRIDE)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.11+-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![YOLOv11](https://img.shields.io/badge/YOLOv11-Ultralytics-111F68?style=flat-square)](https://ultralytics.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=white)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5.0+-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4+-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![Spec Kit](https://img.shields.io/badge/Spec%20Kit-SDD-2ea44f?style=flat-square)](https://github.com/github/spec-kit)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-ff6b35?style=flat-square&logo=anthropic&logoColor=white)](https://claude.ai/code)
[![PRs Open](https://img.shields.io/github/issues-pr/vagnerbarbosa/hackathon-fiap-fase-5?style=flat-square&color=blue)](https://github.com/vagnerbarbosa/hackathon-fiap-fase-5/pulls)
[![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-yellow.svg?style=flat-square)](https://huggingface.co/spaces)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

**Sistema automatizado de modelagem de ameaças STRIDE a partir de diagramas de arquitetura de software usando Visão Computacional e IA.**

> **📅 Atualizado**: 2026-07-12 | **Versão**: 0.2.0 | **Status**: MVP - Frontend com testes e preview de imagem

---

## 🎯 Objetivo

Sistema para **identificação automática de componentes de arquitetura de software em imagens** e **modelagem de ameaças baseada na metodologia STRIDE** (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).

O sistema recebe um diagrama de arquitetura, detecta componentes (usuários, APIs, bancos de dados, filas, etc.) via YOLOv11n, aplica STRIDE programaticamente, busca vulnerabilidades conhecidas (CVE/CWE) e gera um relatório estruturado com contramedidas.

### Pipeline da Solução

```
Imagem de Arquitetura
        |
        v
[Upload + Pré-processamento]
        |
        v
[Detecção de Componentes] → YOLOv11n
        |
        v
[Análise STRIDE] → S, T, R, I, D, E
        |
        v
[Busca de Vulnerabilidades] → CVE / CWE
        |
        v
[Geração de Relatório] → Markdown / JSON / HTML
```

---

## 🚀 Deploy

[![Deploy Status](https://img.shields.io/badge/Deploy-Local%20Dev-2ea44f?style=flat-square&logo=docker)](http://localhost:8001/health)

### Ambientes

| Ambiente | URL | Status |
|----------|-----|--------|
| Healthcheck | `http://localhost:8001/health` | 🟢 Online |
| Swagger UI | `http://localhost:8001/docs` | 🟢 Documentação API |
| Frontend | `http://localhost:5173` | 🟢 Interface Web (Vite Dev) |

---

## 🛠️ Tecnologias

| Camada | Tecnologia | Propósito |
|--------|-----------|-----------|
| 🌐 **API** | FastAPI + Pydantic v2 | Endpoints REST para upload e relatórios |
| 🧠 **Detecção** | YOLOv11n (Ultralytics) | Detecção de componentes em diagramas |
| 🔥 **Framework IA** | PyTorch + torchvision | Treinamento supervisionado do modelo |
| 🎨 **CV** | OpenCV | Pré-processamento de imagens |
| 🗄️ **Banco** | PostgreSQL + SQLAlchemy 2.0 | Persistência de jobs e relatórios |
| ⚡ **Cache** | Redis | Cache de resultados e rate limiting |
| 💻 **Frontend** | React + TypeScript + Vite + Tailwind | Interface web moderna e responsiva |
| 🎨 **UI** | Tailwind CSS + Lucide Icons | Design system customizado |
| 📦 **Container** | Docker + Docker Compose | Orquestração de serviços |

---

## 📁 Estrutura do Projeto

```
├── src/                          # Código fonte Python (FastAPI)
│   ├── api/                      # Rotas FastAPI, controllers, DTOs
│   ├── core/                     # Configurações, segurança, logging
│   ├── services/                 # Casos de uso (detecção, STRIDE, relatórios)
│   ├── infrastructure/           # Adaptadores (DB, ML, cache)
│   ├── models/                   # Entidades de domínio (ORM)
│   └── workers/                  # Processamento assíncrono
├── tests/                        # Testes
│   ├── unit/                     # Testes isolados
│   ├── integration/              # Testes de integração
│   └── e2e/                      # Testes end-to-end
├── frontend/                     # Aplicação React (TypeScript + Vite)
│   ├── src/                      # Código fonte React
│   │   ├── components/           # Componentes React
│   │   ├── App.tsx               # Componente principal
│   │   ├── main.tsx              # Entry point
│   │   └── index.css             # Estilos globais
│   ├── public/                   # Assets estáticos
│   ├── dist/                     # Build de produção
│   ├── Dockerfile                # Container do frontend
│   ├── nginx.conf                # Config Nginx
│   ├── package.json              # Dependências npm
│   ├── tailwind.config.js        # Config Tailwind
│   ├── vite.config.ts            # Config Vite
│   └── tsconfig.json             # Config TypeScript
├── scripts/                      # Scripts de automação
│   ├── start-stride.sh           # Start Linux/macOS
│   ├── start-stride.ps1          # Start Windows (PowerShell)
│   └── start-stride.py            # Start Python (cross-platform)
├── specs/                        # Especificações SpeckIt
│   └── features/                 # Specs de features
├── docs/                         # Documentação
│   ├── sdd.md                    # Software Design Document
│   └── divisao-de-trabalho.md    # Divisão da equipe
├── models/                       # Modelos YOLO treinados
├── storage/                      # Uploads temporários
├── logs/                         # Logs da aplicação
├── docker-compose.yml            # Orquestração Docker
├── Dockerfile                    # Container da API
├── pyproject.toml                # Dependências Python
├── CLAUDE.md                     # Instruções para Claude Code
└── README.md                     # Este arquivo
```

---

## 📊 Dataset

O dataset de treinamento (4.190 imagens, 32 classes) não está versionado no Git devido ao tamanho. Para baixar:

```bash
# Instalar dependência
pip install huggingface_hub

# Baixar dataset
python scripts/download_dataset.py
```

Ou clone diretamente do HuggingFace:
```bash
git clone https://huggingface.co/datasets/fiap-grupo27/architecture-diagrams-stride dataset/
```

O dataset inclui:
- **4.190 imagens** de diagramas de arquitetura AWS/Azure
- **32 classes** de componentes (actor_user, edge_waf, compute_service, data_database, etc.)
- **Augmentations**: BW, blur, noise, jpeg compression, gamma correction
- **Formato YOLO**: Labels em `dataset/{train,val,test}/labels/`

---

## 🚦 Como Executar

### Pré-requisitos

- Docker + Docker Compose
- Git
- 8GB+ RAM (16GB recomendado para treinamento)
- **Dataset baixado** (veja seção 📊 Dataset acima)

### 1. Clone o repositório

```bash
git clone https://github.com/vagnerbarbosa/hackathon-fiap-fase-5.git
cd hackathon-fiap-fase-5
```

### 2. Configure o ambiente

```bash
cp .env.example .env
```

> **Nota:** Para rodar localmente com Docker, os valores padrão em `.env` já estão configurados e funcionam sem alterações. Você só precisa editar o arquivo se:
> - Quiser personalizar as credenciais do banco de dados
> - Estiver rodando em ambiente de produção
> - Precisar configurar uma API Key específica

### 3. Inicie a API (escolha seu método)

#### 🚀 Opção 1: Script Automático (Recomendado)

**Linux/macOS:**
```bash
./scripts/start-stride.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\start-stride.ps1
```

**Python (Cross-platform):**
```bash
# Funciona em qualquer sistema com Python 3
python scripts/start-stride.py
```

**Makefile (Linux/macOS):**
```bash
make start
```

#### 🐳 Opção 2: Docker Compose Manual

```bash
# Build e start
docker-compose up --build -d

# Executar migrações (primeira vez)
docker-compose exec api alembic upgrade head
```

### Opções do Script

```bash
# Modo rápido (sem rebuild)
./scripts/start-stride.sh --no-build

# Modo foreground (ver logs em tempo real)
./scripts/start-stride.sh --foreground

# Sem migrações automáticas
./scripts/start-stride.sh --no-migrations
```

### 5. Teste a API

```bash
# Health check (público)
curl http://localhost:8001/health

# API protegida (requer API Key)
curl -H "X-API-Key: sua-api-key" \
  http://localhost:8001/api/v1/threat-model/analyze
```

> 💡 **Dica**: Disponibilizamos coleções de API para importar em clientes como Postman, Bruno ou Insomnia. Veja [`docs/API-Collection-README.md`](docs/API-Collection-README.md) para mais detalhes.

### 6. Inicie o Frontend (opcional)

O frontend React fornece uma interface web para upload de diagramas e visualização dos resultados. Além de visualizar as ameaças detectadas, é possível exportar os relatórios para os formatos Markdown, JSON, HTML, CSV e PDF.

#### 🚀 Opção 1: Via Docker Compose (Recomendado)

O frontend já está incluído no `docker-compose.yml` e será iniciado junto com a API:

```bash
# O frontend sobe automaticamente na porta 5173
docker compose up frontend -d

# Ou para rebuildar após alterações
docker compose build frontend --no-cache
docker compose up frontend -d
```

Acesse: http://localhost:5173

#### 💻 Opção 2: Desenvolvimento Local (Node.js)

Para desenvolvimento com hot-reload:

```bash
cd frontend

# Instalar dependências
npm install

# Criar .env.local (opcional)
cp .env.example .env

# Iniciar servidor de desenvolvimento
npm run dev
```

Acesse: http://localhost:5173

**Requisitos:**
- Node.js 18+
- npm 9+

#### 🧪 Executar Testes do Frontend

```bash
cd frontend

# Executar todos os testes
npm test

# Executar com cobertura
npm run test:coverage

# Modo watch (durante desenvolvimento)
npm run test:watch
```

### Endpoints disponíveis

| Endpoint | Método | Auth | Descrição |
|----------|--------|------|-----------|
| `/health` | GET | ❌ | Health check com status do DB |
| `/docs` | GET | ❌ | Swagger UI (documentação) |
| `/version` | GET | ❌ | Versão da API |
| `/api/v1/threat-model/analyze` | POST | ✅ | Inicia análise (placeholder) |
| `/api/v1/threat-model/{id}` | GET | ✅ | Status da análise (placeholder) |
| `/api/v1/threat-model/{id}/report` | GET | ✅ | Relatório (placeholder) |

> **Nota**: Autenticação via header `X-API-Key`. Defina em `.env`.

---

### 🛠️ Comandos Úteis (Makefile)

Disponíveis em Linux/macOS (requer `make`):

```bash
# Iniciar a API
make start

# Início rápido (sem rebuild)
make start-quick

# Ver logs em tempo real
make logs

# Parar a API
make stop

# Executar migrações
make migrate

# Criar nova migração
make migrate-create msg="descrição"

# Executar testes
make test

# Testes com cobertura
make test-cov

# Limpar containers e arquivos temporários
make clean

# Ver todos os comandos
make help
```

---

## 📊 Metodologia STRIDE

| Categoria | Ameaça | Propriedade Violada |
|-----------|--------|---------------------|
| **S** | Spoofing | Autenticação |
| **T** | Tampering | Integridade |
| **R** | Repudiation | Não-repudiação |
| **I** | Information Disclosure | Confidencialidade |
| **D** | Denial of Service | Disponibilidade |
| **E** | Elevation of Privilege | Autorização |

---

## 📋 Checklist de Desenvolvimento

- [x] Definição do tema e regras do hackathon
- [x] Especificações SpeckIt (8 features)
- [x] SDD consolidado
- [x] **Spec 000**: Contratos de Domínio (Pydantic Models) (✅ Concluída)
- [x] **Spec 001**: API Core + Scaffolding (FastAPI, Docker, PostgreSQL) (✅ Concluída)
- [x] **Spec 002**: Dataset e Treinamento YOLO (em desenvolvimento)
- [x] **Spec 003**: Serviço de Detecção de Componentes (✅ Concluída)
- [x] **Spec 004**: Motor STRIDE (✅ Concluída)
- [x] **Spec 005**: Vulnerabilidades e Contramedidas (✅ Concluída)
- [ ] **Spec 006**: Gerador de Relatórios (pendente)
- [x] **Spec 007**: CI/CD GitHub Actions (✅ Concluída)
- [x] **Spec 008**: Frontend React (✅ Concluída)
- [ ] **Spec 009**: Roteiro do Vídeo (bloqueado)

---

## 🤝 Contribuição

Este projeto segue o fluxo de **Pull Requests** rigoroso:

1. Crie uma branch a partir da `main`: `git checkout -b feature/nome-da-spec`
2. Faça seus commits seguindo [Conventional Commits](https://www.conventionalcommits.org/)
3. Abra um Pull Request para `main`
4. Aguarde review e CI passando antes do merge

> ⚠️ **Nunca commitar diretamente na `main`.**

---

## 👥 Integrantes Grupo 27

- **Adriel Santos** — [@AdrielCandido](https://github.com/AdrielCandido)
- **Leticia Nepomucena** — [@LeticiaNepomucena](https://github.com/LeticiaNepomucena)
- **Lucas Silva** — [@lucfsilva](https://github.com/lucfsilva)
- **Vagner Barbosa** — [@vagnerbarbosa](https://github.com/vagnerbarbosa)

---

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

Copyright (c) 2026 Grupo 27 Hackathon - FIAP

---

## 🔒 Segurança

Para reportar vulnerabilidades, consulte nossa [Política de Segurança](SECURITY.md).

---

> **Desenvolvido para o Hackathon FIAP Fase 5 — FIAP Software Security**
