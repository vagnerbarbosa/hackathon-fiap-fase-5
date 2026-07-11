# Spec 008: Frontend React — Interface de Usuário

---

## Contexto / Motivação

A API de modelagem de ameaças precisa de uma interface web amigável para facilitar o upload de diagramas, acompanhamento do processamento e visualização dos relatórios de vulnerabilidades. Uma interface React proporciona experiência moderna, responsiva e interativa.

## Objetivo

Criar uma aplicação frontend em React que permita:
1. Upload de imagens de arquitetura (PNG, JPG, JPEG)
2. Acompanhamento visual do processamento (loading/estado do job)
3. Visualização completa do relatório de vulnerabilidades STRIDE
4. Exportação do relatório em múltiplos formatos (JSON, Markdown, HTML, PDF, CSV)

## Requisitos Funcionais

### RF-001: Upload de Diagrama
- **Dado** que o usuário acessa a aplicação
- **Quando** ele seleciona uma imagem de arquitetura (PNG, JPG, JPEG)
- **Então** o sistema valida o tipo e tamanho (máx 50MB) e envia para API
- **E** exibe uma prévia da imagem selecionada
- **E** mostra mensagem de erro se o formato for inválido

### RF-002: Tela de Loading/Processamento
- **Dado** que o upload foi realizado com sucesso
- **Quando** o job é criado na API
- **Então** exibe componente de loading animado
- **E** mostra status em tempo real (pending → processing → completed/failed)
- **E** permite cancelar/polling automático para atualização de status

### RF-003: Visualização do Relatório Completo
- **Dado** que o processamento foi concluído
- **Quando** o relatório está disponível
- **Então** exibe data e hora da geração do relatório
- **E** mostra a imagem original analisada
- **E** lista todos os componentes detectados
- **E** exibe a matriz STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation of Privilege)
- **E** mostra ameaças identificadas com severidade
- **E** apresenta vulnerabilidades (CVEs/CWEs) e contramedidas

### RF-004: Exportação de Relatórios
- **Dado** que o relatório está sendo visualizado
- **Quando** o usuário clica nos botões de exportação
- **Então** permite download nos formatos: JSON, Markdown, HTML, PDF, CSV
- **E** cada formato deve conter todos os dados do relatório

## Requisitos Não-Funcionais

### RNF-001: Tecnologia
- Framework: React 18+ com TypeScript
- Build Tool: Vite
- UI Library: Tailwind CSS + Headless UI
- HTTP Client: Axios
- State Management: React Query (TanStack Query) para cache de API
- Icons: Lucide React

### RNF-002: UX/UI
- Design responsivo (mobile, tablet, desktop)
- **Tema escuro com identidade visual FIAP** (rosa #ED145B)
- Fonte: Montserrat (primária), Inter (secundária)
- Feedback visual em todas as ações
- Acessibilidade (ARIA labels, navegação por teclado)

### RNF-003: Performance
- Lazy loading de componentes
- Otimização de imagens
- Cache de requisições à API

### RNF-004: Segurança
- Sanitização de inputs
- HTTPS obrigatório em produção
- Não expor credenciais ou tokens no código

### RNF-005: Branding
- Paleta de cores FIAP:
  - Rosa FIAP: `#ED145B` (primária)
  - Rosa claro: `#F05A85` (hover)
  - Rosa escuro: `#C4124D` (variações)
  - Preto: `#1A1A1A` (fundo)
  - Cinza 900: `#0f172a` (background)
- Logo FIAP STRIDE no header
- Explicação do STRIDE na página inicial
- Integrantes do Grupo 27 com links GitHub
- Copyright e nota de privacidade no footer

## Critérios de Aceitação (Gherkin)

### Cenário: Upload bem-sucedido
```gherkin
Dado que estou na página inicial
Quando seleciono uma imagem "arquitetura.png" válida
E clico no botão "Analisar"
Então vejo uma prévia da imagem
E sou redirecionado para a tela de processamento
E o job é criado na API
```

### Cenário: Formato de arquivo inválido
```gherkin
Dado que estou na página inicial
Quando seleciono um arquivo "documento.pdf"
Então vejo a mensagem de erro "Formato inválido. Use PNG, JPG ou JPEG."
E o botão "Analisar" permanece desabilitado
```

### Cenário: Visualização do relatório completo
```gherkin
Dado que o job "job-123" foi concluído
Quando sou redirecionado para a página de relatório
Então vejo a data/hora "09/07/2026 14:30:15" de geração
E vejo a imagem original carregada
E vejo a lista de 5 componentes detectados
E vejo a matriz STRIDE preenchida
E vejo as 12 ameaças identificadas
```

### Cenário: Exportação para múltiplos formatos
```gherkin
Dado que estou visualizando um relatório completo
Quando clico no botão "Exportar JSON"
Então o download do arquivo "relatorio-job-123.json" inicia
Quando clico no botão "Exportar PDF"
Então o download do arquivo "relatorio-job-123.pdf" inicia
```

## Estrutura de Telas

### Tela 1: Home / Upload
```
+--------------------------------------------------+
|  Logo FIAP STRIDE    Grupo 27  [Análise] [Sobre] |
+--------------------------------------------------+
|                                                  |
|         Modelagem de Ameaças com IA              |
|              Upload de Arquitetura               |
|                                                  |
|      +------------------------------------+      |
|      |                                    |      |
|      |      [Ícone de Upload]             |      |
|      |                                    |      |
|      |   Arraste ou clique para           |      |
|      |   selecionar imagem                |      |
|      |                                    |      |
|      |   PNG, JPG, JPEG - Máx 50MB        |      |
|      |                                    |      |
|      +------------------------------------+      |
|                                                  |
|            [    Analisar    ]                    |
|                   (desabilitado até upload)      |
+--------------------------------------------------+
|                                                  |
|  O que é STRIDE?                                 |
|  [S] Spoofing      [T] Tampering      [R] Repudiation |
|  [I] Information   [D] Denial of       [E] Elevation  |
|      Disclosure         Service             of Privilege |
|                                                  |
+--------------------------------------------------+
|  © 2026 FIAP STRIDE - Grupo 27                   |
|  Este site não coleta dados pessoais...           |
+--------------------------------------------------+
```

### Tela 2: Sobre o Projeto
```
+--------------------------------------------------+
|  Logo FIAP STRIDE    Grupo 27  [Análise] [Sobre] |
+--------------------------------------------------+
|                                                  |
|  Sobre o Projeto                                 |
|  Explicação do FIAP STRIDE...                     |
|                                                  |
|  Metodologia STRIDE                              |
|  [Lista das 6 categorias com cores]              |
|                                                  |
|  Grupo 27                                        |
|  Descrição do grupo...                            |
|                                                  |
|  Integrantes                                     |
|  +---------------+  +---------------+           |
|  | Adriel Santos |  | Leticia       |           |
|  | @AdrielCandido|  | @LeticiaNep...|           |
|  +---------------+  +---------------+           |
|  +---------------+  +---------------+           |
|  | Lucas Silva   |  | Vagner        |           |
|  | @lucfsilva    |  | @vagnerbarbosa|           |
|  +---------------+  +---------------+           |
|                                                  |
|  Repositório                                     |
|  [github.com/vagnerbarbosa/hackathon-fiap-fase-5]|
|                                                  |
|  Tecnologias Utilizadas                          |
|  [FastAPI] [React] [TypeScript] [Tailwind] ...   |
|                                                  |
+--------------------------------------------------+
|  © 2026 FIAP STRIDE - Grupo 27                   |
+--------------------------------------------------+
```

### Tela 3: Processando
```
+--------------------------------------------------+
|  Logo FIAP STRIDE    Grupo 27  [Cancelar]        |
+--------------------------------------------------+
|                                                  |
|              Analisando Arquitetura              |
|                                                  |
|              ╭──────────────╮                    |
|             (    🔄      )                      |
|              ╰──────────────╯                    |
|                                                  |
|              [████████░░░░] 60%                  |
|                                                  |
|              Status: detectando componentes...   |
|                                                  |
|              Job ID: job-123                     |
|              Iniciado: 14:28:00                  |
|              Tempo decorrido: 00:02:15           |
|                                                  |
+--------------------------------------------------+
|  Logs de processamento:                          |
|  [14:28:05] Upload concluído                     |
|  [14:28:10] Detectando componentes...           |
|  [14:29:00] Aplicando STRIDE...                 |
|  [14:29:30] Buscando vulnerabilidades...        |
+--------------------------------------------------+
```

### Tela 4: Relatório Completo
```
+--------------------------------------------------+
|  Logo FIAP    [Voltar]    [Exportar ▼]    [Tema] |
+--------------------------------------------------+
|                                                  |
|  Relatório de Vulnerabilidades        📅 09/07   |
|                                       🕐 14:30   |
|  Job: #123 | Status: ✅ Concluído                |
|                                                  |
+--------------------------------------------------+
|  IMAGEM ORIGINAL  |  COMPONENTES DETECTADOS     |
|  [thumbnail]      |  • Load Balancer             |
|                   |  • API Gateway               |
|                   |  • Auth Service              |
|                   |  • Database                  |
|                   |  • Payment Service           |
+--------------------------------------------------+
|  MATRIZ STRIDE                                   |
|  +----------+---+---+---+---+---+---+            |
|  |Componente| S | T | R | I | D | E |            |
|  +----------+---+---+---+---+---+---+            |
|  |Load Balan| ✓ | ✓ |   |   | ✓ |   |            |
|  |API Gatewa| ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |            |
|  |Auth Servi| ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |            |
|  +----------+---+---+---+---+---+---+            |
+--------------------------------------------------+
|  AMEAÇAS IDENTIFICADAS (12)                     |
|  ┌──────────────────────────────────────────┐   |
|  │ 🔴 Alta  | Spoofing | Auth Service      │   |
|  │    CWE-287 | Autenticação impropriada  │   |
|  │    [Ver contramedida OWASP]              │   |
|  └──────────────────────────────────────────┘   |
|  ┌──────────────────────────────────────────┐   |
|  │ 🟡 Média | Tampering | Database         │   |
|  │    CWE-20  | Validação de input         │   |
|  │    [Ver contramedida OWASP]              │   |
|  └──────────────────────────────────────────┘   |
+--------------------------------------------------+
|  BOTÕES DE EXPORTAÇÃO:                           |
|  [JSON] [Markdown] [HTML] [PDF] [CSV]            |
+--------------------------------------------------+
```

## Contratos de API (Consumo)

### Endpoints Utilizados

```typescript
// Criar job de análise
POST /api/v1/threat-model/analyze
Content-Type: multipart/form-data
Body: { file: File }
Response: { job_id: string, status: "pending" }

// Consultar status do job
GET /api/v1/threat-model/{job_id}
Response: {
  job_id: string,
  status: "pending" | "processing" | "completed" | "failed",
  created_at: string,
  updated_at: string,
  error_message?: string
}

// Obter relatório
GET /api/v1/threat-model/{job_id}/report?format=md|json
Response: Relatório em formato solicitado

// Download de arquivo estático
GET /reports/{job_id}.{format}
```

## Estrutura de Diretórios Implementada

```
frontend/
├── public/
│   └── vite.svg
├── src/
│   ├── components/
│   │   └── ui/                # Componentes base (shadcn/ui style)
│   ├── api/                   # Configuração de API (axios)
│   ├── hooks/                 # React hooks
│   ├── types/                 # TypeScript types
│   ├── utils/                 # Utilitários
│   ├── App.tsx               # Componente principal com rotas
│   ├── App.css               # Estilos específicos
│   ├── index.css             # Estilos globais + fonte FIAP
│   ├── main.tsx              # Entry point
│   └── vite-env.d.ts         # Tipos Vite
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── tailwind.config.js         # Config com cores FIAP
├── postcss.config.js
├── vite.config.ts
├── Dockerfile                 # Multi-stage build com Nginx
└── nginx.conf                 # Config Nginx + proxy API
```

## Dependências

### Pré-requisitos
- **Spec 000** — consome os contratos de domínio (`ArchitectureGraph`, `Threat`, `EnrichedThreat`, `Job`)
- **Spec 001** — depende da API estar implementada e funcionando
- **Spec 006** — depende do gerador de relatórios para visualização

### Internas
- API em `http://localhost:8000` (ou URL configurada via env)

### Pacotes npm
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.1",
    "react-query": "^3.39.3",
    "axios": "^1.6.2",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "@typescript-eslint/eslint-plugin": "^6.14.0",
    "@typescript-eslint/parser": "^6.14.0",
    "typescript": "^5.2.2",
    "vite": "^5.0.8",
    "tailwindcss": "^3.3.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "eslint": "^8.55.0"
  }
}
```

## Checklist de Implementação

- [x] Configurar projeto Vite + React + TypeScript
- [x] Configurar Tailwind CSS
- [x] Configurar React Query
- [x] Implementar componente UploadZone (placeholder)
- [x] Implementar validação de arquivo (tipo, tamanho) - preparado
- [x] Implementar tela de loading (placeholder)
- [x] Implementar visualizador de relatório (placeholder)
- [x] **Implementar identidade visual FIAP** (rosa #ED145B, fonte Montserrat)
- [x] **Adicionar explicação do STRIDE na página inicial**
- [x] **Adicionar integrantes do Grupo 27 com links GitHub**
- [x] **Adicionar copyright e nota de privacidade**
- [x] Configurar variáveis de ambiente (API_URL)
- [x] Criar Dockerfile para frontend
- [x] Criar nginx.conf com proxy para API
- [x] Adicionar ao docker-compose.yml principal
- [ ] Implementar integração real com API (upload, polling, relatório)
- [ ] Implementar botões de exportação (JSON, MD, HTML, PDF, CSV)
- [ ] Testes E2E com Cypress ou Playwright

## Notas

- O frontend está funcional como MVP com layout completo e identidade FIAP
- A integração real com a API está preparada mas requer os endpoints implementados
- Exportação PDF pode ser feita via biblioteca (jsPDF, html2canvas) ou API externa
- O polling para status do job deve ter backoff exponencial (1s, 2s, 5s, 10s)
- Cache de relatórios no React Query para navegação rápida
- **A cor rosa FIAP (#ED145B) é usada em todo o tema para manter identidade visual**

---

*Spec atualizada em: 2026-07-11*
*Implementado: Layout completo, identidade FIAP, STRIDE, Grupo 27*
*Depende de: Spec 001 (API Core), Spec 006 (Report Generator)*
