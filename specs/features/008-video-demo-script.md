# Spec: Roteiro e Estrutura do Vídeo de Apresentação

---

## Contexto / Motuação

O hackathon exige um **vídeo de até 15 minutos** explicando a solução proposta. Um roteiro bem estruturado garante que todas as partes importantes sejam cobertas e que o vídeo seja persuasivo para os avaliadores.

## Objetivo

Criar um roteiro detalhado (script) para gravação do vídeo, cobrindo:
1. Introdução ao problema e contexto de segurança.
2. Demonstração da solução (end-to-end).
3. Explicação técnica das decisões arquiteturais.
4. Resultados e validação com arquiteturas de teste.
5. Considerações finais e próximos passos.

## Estrutura do Vídeo (15 min)

### Parte 1: Introdução (2 min)
**Conteúdo**:
- Apresentação da equipe (nomes, roles).
- Contexto: FIAP Software Security e o desafio de modelagem de ameaças manual.
- Problema: arquitetos gastam horas identificando vulnerabilidades; erros humanos são comuns.
- Solução proposta: IA para modelagem de ameaças STRIDE automatizada.

**Slides/Telas**:
- Logo FIAP + título do projeto
- Slide com estatísticas sobre falhas de segurança em arquiteturas
- Diagrama do pipeline proposto (imagem → componentes → STRIDE → relatório)

### Parte 2: Demonstração End-to-End (6 min)
**Conteúdo**:
1. Upload de uma imagem de arquitetura para a API (`POST /api/v1/threat-model/analyze`).
2. Acompanhamento do job (`GET /api/v1/threat-model/{id}`).
3. Consulta do relatório (`GET /api/v1/threat-model/{id}/report`).
4. Visualização do relatório Markdown gerado.

**Slides/Telas**:
- Terminal mostrando `curl` ou Swagger UI (`/docs`)
- JSON de resposta com componentes detectados
- Relatório Markdown renderizado (matriz STRIDE, ameaças, contramedidas)
- Opcional: side-by-side com a imagem original

### Parte 3: Explicação Técnica (4 min)
**Conteúdo**:
1. **Dataset e Treinamento**: como geramos/ coletamos imagens, anotamos, e treinamos YOLOv8.
2. **Detecção**: como o modelo identifica componentes e infere relacionamentos.
3. **STRIDE**: como o motor aplica as 6 categorias de ameaças.
4. **Vulnerabilidades**: como enriquecemos com CWEs e contramedidas.
5. **Arquitetura do Sistema**: diagrama da própria solução (FastAPI + PostgreSQL + Redis + YOLO).

**Slides/Telas**:
- Exemplos de imagens do dataset
- Gráfico de treinamento (mAP por epoch)
- Diagrama da arquitetura do sistema (meta-arquitetura)
- Código-fonte destacando o StrideEngine ou a API

### Parte 4: Validação com Arquiteturas de Teste (2 min)
**Conteúdo**:
- Mostrar as 2 arquiteturas de teste fornecidas pelo hackathon.
- Executar a análise em ambas.
- Comparar resultados: componentes detectados, ameaças encontradas, contramedidas sugeridas.
- Destacar acertos e limitações conhecidas.

**Slides/Telas**:
- Arquitetura 1: antes (imagem) → depois (relatório)
- Arquitetura 2: antes (imagem) → depois (relatório)
- Tabela comparativa de métricas

### Parte 5: Conclusão (1 min)
**Conteúdo**:
- Resumo do impacto: economia de tempo, redução de erros humanos, padronização.
- Próximos passos: suporte a mais tipos de diagramas, integração com CI/CD pipelines, LLM para descrições mais ricas.
- Agradecimentos.
- Link do GitHub na tela final.

**Slides/Telas**:
- Slide de resumo (3 bullets de impacto)
- Slide de roadmap (3 próximos passos)
- Slide final: QR code + link do GitHub

## Roteiro Detalhado (Script)

### [0:00–0:30] Abertura
```
"Olá! Somos [Nomes] e este é o projeto de Modelagem de Ameaças com IA,
desenvolvido para o Hackathon FIAP Fase 5.
Segurança de software não pode ser uma reflexão tardia — ela precisa
começar na arquitetura. Mas modelar ameaças manualmente é lento e propenso
a erros. Nossa solução automatiza isso."
```

### [0:30–2:00] Contexto e Problema
```
"A metodologia STRIDE — Spoofing, Tampering, Repudiation, Information
Disclosure, Denial of Service, Elevation of Privilege — é o padrão ouro
para modelagem de ameaças. Mas aplicar STRIDE em um diagrama de 10
componentes leva horas. Nosso sistema faz isso em segundos."
```

### [2:00–8:00] Demonstração
```
"Vamos ver na prática. Tenho aqui um diagrama de arquitetura de um
sistema de e-commerce. Vou fazer upload para nossa API..."
[mostrar curl ou Swagger UI]
"O sistema detectou 6 componentes: usuário, load balancer, API, fila,
database, e serviço de pagamento externo."
[mostrar JSON]
"Agora vamos ver o relatório STRIDE gerado automaticamente..."
[mostrar Markdown renderizado]
"Aqui temos a matriz STRIDE, as ameaças detalhadas com CWEs, e as
contramedidas sugeridas com links para OWASP."
```

### [8:00–12:00] Tecnologia
```
"Como funciona por baixo?"
[explicar cada camada em 1 minuto]
```

### [12:00–14:00] Validação
```
"E funciona para arquiteturas reais? Testamos com as arquiteturas de
validação do hackathon..."
[mostrar resultados]
```

### [14:00–15:00] Fechamento
```
"Nosso sistema transforma modelagem de ameaças de uma tarefa manual
de horas em um processo automatizado de segundos. O código está
disponível no GitHub. Obrigado!"
```

## Requisitos Técnicos do Vídeo

| Item | Especificação |
|------|---------------|
| Duração | ≤ 15 minutos |
| Resolução | 1080p (1920x1080) mínimo |
| Áudio | Claro, sem ruído de fundo |
| Legendas | Recomendado (acessibilidade) |
| Formato | MP4 (H.264) |

## Dependências

### Internas
- **Specs 001–006** — o vídeo depende do sistema estar funcional
- **Arquiteturas de teste** — precisa ter as imagens e resultados prontos

### Ferramentas Recomendadas
- OBS Studio (gravação de tela)
- DaVinci Resolve (edição, se necessário)
- Canva ou Figma (slides)
- CapCut ou Descript (legendas automáticas)

## Checklist de Gravação

- [ ] Script revisado e ensaiado
- [ ] Slides criados e exportados
- [ ] Ambiente de demonstração preparado (Docker rodando, dados de teste)
- [ ] Microfone testado
- [ ] Gravação de tela em 1080p
- [ ] Edição final (cortes, transições)
- [ ] Legendas adicionadas
- [ ] Exportação em MP4
- [ ] Upload para Google Drive / YouTube (não listado) / outro serviço
- [ ] Link anotado no README do projeto

---

*Spec criada em: 2026-06-21*
*Nota: Esta spec é mais leve (não tem código), mas é crítica para o entregável do hackathon.*
