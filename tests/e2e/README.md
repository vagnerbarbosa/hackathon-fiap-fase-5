# Testes End-to-End

Este diretório está reservado para testes end-to-end (E2E).

## Decisão atual

No MVP, a cobertura de testes é garantida por:

- **Testes unitários** (`tests/unit/`) para lógica de domínio e serviços isolados.
- **Testes de integração** (`tests/integration/`) para verificar a API FastAPI,
  banco de dados e serviços de inferência.

Testes E2E que subam toda a stack (Docker Compose, frontend e API) serão
adicionados em iterações futuras, após a consolidação dos cenários principais
no ambiente de integração.
