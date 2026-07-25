# Workers

Este diretório está reservado para workers de processamento assíncrono.

## Decisão atual

O MVP utiliza **tarefas assíncronas nativas do FastAPI** (`asyncio.create_task`) para
processar as análises em background após o upload da imagem. Essa abordagem é
suficiente para o volume esperado no hackathon porque:

- Não exige infraestrutura extra (Celery, RabbitMQ, etc.).
- O Redis já presente no stack é usado apenas para cache e rate limiting.
- O tempo de inferência do modelo ONNX é curto, então a resposta `202 Accepted`
  não precisa delegar para um worker dedicado.

## Futuro

Caso o volume de jobs cresça ou seja necessário garantir entrega/retry, este
espaço pode receber um worker baseado em Celery, RQ ou arquitetura similar,
consumindo jobs de uma fila no Redis.
