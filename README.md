# Sistema de Captação de Solicitações via QR Code

Backend FastAPI para captação e rastreamento de solicitações através de QR Codes distribuídos em veículos de parceiros.

## 🏗️ Arquitetura

```
src/
├── api/
│   ├── routers/          # FastAPI route handlers
│   │   ├── leads.py
│   │   ├── parceiros.py
│   │   ├── vendas.py
│   │   └── dashboard.py
│   └── schemas/          # Pydantic models
│       ├── lead.py
│       ├── parceiro.py
│       ├── venda.py
│       ├── dashboard.py
│       └── common.py
├── core/
│   ├── config.py         # Application settings
│   ├── exceptions.py     # Custom exceptions
│   └── logging.py        # Logging configuration
├── db/
│   ├── connection.py     # Firestore connection
│   └── repositories.py   # Base repository
├── services/
│   ├── leads.py          # Lead business logic
│   ├── parceiros.py      # Partner business logic
│   ├── vendas.py         # Sale business logic
│   └── dashboard.py      # Dashboard metrics
└── main.py               # Application entry point
```

## 🚀 Quick Start

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar ambiente

```bash
cp .env.example .env
# Edite .env com suas configurações
```

### 3. Rodar com Firestore Emulator (Desenvolvimento)

```bash
# Terminal 1: Iniciar Firestore Emulator
gcloud beta emulators firestore start --project=demo-project

# Terminal 2: Rodar a API
uvicorn src.main:app --reload
```

### 4. Acessar documentação

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📋 Endpoints Principais

### Parceiros
- `POST /api/v1/parceiros` - Criar parceiro
- `GET /api/v1/parceiros` - Listar parceiros
- `GET /api/v1/parceiros/{id}` - Obter parceiro
- `PATCH /api/v1/parceiros/{id}` - Atualizar parceiro
- `GET /api/v1/parceiros/{id}/resumo` - Resumo do parceiro

### Leads
- `POST /api/v1/leads` - Criar lead
- `GET /api/v1/leads` - Listar leads
- `GET /api/v1/leads/{id}` - Obter lead
- `PATCH /api/v1/leads/{id}` - Atualizar lead

### Vendas
- `POST /api/v1/vendas` - Criar venda
- `GET /api/v1/vendas` - Listar vendas
- `POST /api/v1/vendas/{id}/pagar` - Marcar como paga

### Dashboard
- `GET /api/v1/dashboard/parceiro/{id}` - Dashboard do parceiro
- `GET /api/v1/dashboard/geral` - Dashboard geral (admin)

## 🧪 Testes

```bash
pytest tests/ -v --cov=src
```

## 📦 Deploy (Cloud Run)

```bash
# Build e push da imagem
docker build -t gcr.io/PROJECT_ID/sist-vendas-uber -f deploy/Dockerfile .
docker push gcr.io/PROJECT_ID/sist-vendas-uber

# Deploy
gcloud run deploy sist-vendas-uber \
    --image gcr.io/PROJECT_ID/sist-vendas-uber \
    --region us-central1 \
    --allow-unauthenticated
```

## 🔑 Modelo de Dados (Firestore)

### Coleção: `parceiros`
```json
{
  "id": "UBER_123",
  "nome": "Carlos Silva",
  "telefone": "+559999999999",
  "ativo": true,
  "percentual_comissao": 0.1,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Coleção: `leads`
```json
{
  "id": "lead_001",
  "parceiro_id": "UBER_123",
  "nome": "João",
  "telefone": "+559888888888",
  "origem": "qr_code",
  "status": "novo",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Coleção: `vendas`
```json
{
  "id": "venda_001",
  "lead_id": "lead_001",
  "parceiro_id": "UBER_123",
  "valor_venda": 1200,
  "percentual_comissao": 0.1,
  "comissao": 120,
  "status": "pendente",
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "pago_em": "timestamp"
}
```

## 🛠️ Tecnologias

- **FastAPI** - Framework web moderno
- **Pydantic** - Validação de dados
- **Firestore** - Banco de dados NoSQL
- **Cloud Run** - Deploy serverless
- **uvicorn** - Servidor ASGI

## 📝 License

MIT
