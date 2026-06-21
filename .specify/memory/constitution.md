# Hackathon FIAP Fase 5 — Constitution

## Core Principles

### I. Spec-First Development
Toda funcionalidade começa com uma spec escrita antes do código.
Specs definem O QUÊ e POR QUÊ, não COMO.
Nenhum código é escrito sem uma spec aprovada.

### II. API First
Contratos OpenAPI são definidos antes de implementar endpoints.
Models Pydantic são a fonte da verdade para todos os serviços.

### III. Context7 Mandatory
Toda mudança de código consulta o MCP Context7 para boas práticas atualizadas.
Aplica-se a todas as bibliotecas: FastAPI, Pydantic, PyTorch, Docker, OpenCV, SQLAlchemy.

### IV. Pull Request Only
`main` é protegida. Nunca commitar diretamente.
Tudo passa por branch → PR → review → CI green → merge.

### V. Test-First (TDD)
Testes são escritos antes da implementação.
Coverage mínimo: 70%. Segurança: 80%+.
Ruff + mypy são gates obrigatórios no CI.

### VI. Parallel Work
Contratos de domínio são o primeiro passo (Spec 000).
Mocks/stubs permitem trabalho paralelo sem bloqueio.
Ninguém altera contratos sem avisar o time.

### VII. Observability
Logging estruturado JSON em todos os serviços.
Campos obrigatórios: timestamp, level, module, message, request_id.

### VIII. Security by Default
Rate limiting, headers OWASP, validação de uploads por magic bytes.
Dados sensíveis são anonimizados antes de logar (LGPD).

## Governance

- Esta constitution supersedes todas as outras práticas.
- Emendas requerem PR com justificativa e aprovação de 2 membros.
- Todas as specs devem referenciar esta constitution.

**Version**: 1.0.0 | **Ratified**: 2026-06-21 | **Last Amended**: 2026-06-21
