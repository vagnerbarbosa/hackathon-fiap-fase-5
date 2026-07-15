# 📬 Coleções de API

Este diretório contém arquivos de importação para clientes REST como Postman, Bruno, Insomnia e outros.

---

## 📁 Arquivos Disponíveis

| Arquivo | Formato | Ferramenta |
|---------|---------|------------|
| [`postman-collection.json`](./postman-collection.json) | Postman Collection v2.1 | Postman, Insomnia, Hoppscotch |
| [`bruno-collection/`](./bruno-collection/) | Pasta com arquivos `.bru` | [Bruno](https://www.usebruno.com/) |

---

## 🚀 Como Importar

### Postman

1. Abra o Postman
2. Clique em **Import** (botão no canto superior esquerdo)
3. Selecione o arquivo `postman-collection.json`
4. Configure as variáveis de ambiente:
   - `base_url`: `http://localhost:8001`
   - `api_key`: `your-secure-api-key-here`
   - `job_id`: Deixe vazio inicialmente (será preenchido pelo endpoint de upload)

---

### Bruno (Recomendado)

[Bruno](https://www.usebruno.com/) é um cliente REST open-source, mais leve e rápido que o Postman, com suporte nativo a Git.

1. Instale o Bruno: `npm install @usebruno/cli -g` ou baixe em [usebruno.com](https://www.usebruno.com/)
2. Abra a pasta do projeto no Bruno:
   ```bash
   cd docs/bruno-collection
   bruno
   # ou
   code .  # se usar VS Code com extensão Bruno
   ```
3. Selecione o ambiente **local** no dropdown superior
4. Execute as requests!

**Estrutura da coleção Bruno:**
```
bruno-collection/
├── bruno.json              # Config da coleção
├── environments/
│   └── local.bru           # Variáveis: base_url, api_key, job_id
├── Health Check/
│   ├── Verificar Saúde da API.bru
│   └── Endpoint Raiz.bru
├── Threat Model/
│   ├── Upload e Análise de Imagem.bru
│   ├── Consultar Status do Job.bru
│   ├── Obter Relatório JSON.bru
│   └── Obter Relatório HTML.bru
└── Documentação/
    ├── Swagger UI.bru
    ├── ReDoc.bru
    └── OpenAPI Schema.bru
```

---

### Insomnia

1. Abra o Insomnia
2. Clique em **Application** → **Preferences** → **Data** → **Import Data**
3. Selecione `From File` e escolha `postman-collection.json`

---

## 🔧 Endpoints Incluídos

### Health Check
- `GET /health` - Verifica saúde da API e banco
- `GET /` - Endpoint raiz

### Threat Model
- `POST /api/v1/threat-model/analyze` - Upload de imagem e análise STRIDE
- `GET /api/v1/threat-model/{job_id}` - Consulta status do job
- `GET /api/v1/threat-model/{job_id}/report?format=json` - Relatório JSON
- `GET /api/v1/threat-model/{job_id}/report?format=html` - Relatório HTML

### Documentação
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc
- `GET /openapi.json` - Schema OpenAPI

---

## 🔐 Autenticação

Todas as rotas protegidas requerem o header:
```
X-API-Key: your-secure-api-key-here
```

**Variável**: `{{api_key}}`

---

## 📋 Fluxo de Uso Típico

1. **Verificar saúde**: `GET /health`
2. **Upload imagem**: `POST /api/v1/threat-model/analyze`
   - Copie o `job_id` retornado
   - Atualize a variável `{{job_id}}` na coleção
3. **Acompanhar status**: `GET /api/v1/threat-model/{{job_id}}`
   - Repita até `status: completed`
4. **Obter relatório**: `GET /api/v1/threat-model/{{job_id}}/report`

---

## 🐛 Exemplos de Respostas

### Upload (202 Accepted)
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Análise iniciada. Use GET /threat-model/{job_id} para acompanhar o progresso."
}
```

### Status (200 OK)
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "input_image_path": "uploads/upload_diagrama.png",
  "output_report_path": "reports/550e8400-e29b-41d4-a716-446655440000.md",
  "error_message": null,
  "created_at": "2026-07-14T20:00:00",
  "updated_at": "2026-07-14T20:00:10"
}
```

### Erro - Baixa Confiança (422)
```json
{
  "detail": "Não foi possível detectar componentes na imagem. A imagem não parece ser um diagrama de arquitetura válido."
}
```

---

## 📚 Mais Informações

- [Documentação Swagger](../src/api/main.py) - Execute a API e acesse `/docs`
- [SDD - Software Design Document](./sdd.md)
- [Especificações](./features/)
