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



# 🚀 Deploy de Produção - Sistema de Vendas de Saúde (FastAPI + Cloud Run)

Este documento descreve o fluxo completo de deploy e operação do backend em produção utilizando:

- **FastAPI**
- **Google Cloud Run**
- **Cloud Build**
- **Artifact Registry**
- **Firestore**
- **Firebase Hosting (Frontend)**

---

# Arquitetura

```text
GitHub (main)
        ↓
Cloud Build
        ↓
Artifact Registry
        ↓
Cloud Run (FastAPI)
        ↓
Firestore
        ↓
Frontend Vue (Firebase Hosting)
```
Projeto Google Cloud:

qr-saude-alpha

Região:

southamerica-east1 (São Paulo)
Pré-requisitos

Instalar:

Docker Desktop
Google Cloud CLI
Git

Autenticar:

gcloud auth login
gcloud auth application-default login

Definir projeto:

gcloud config set project qr-saude-alpha

Verificar:

gcloud config get-value project

Resultado esperado:

qr-saude-alpha
Habilitar APIs necessárias
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
Estrutura de Produção
Backend
Cloud Run
Service: qr-saude-api
Frontend
Firebase Hosting
Banco de Dados
Firestore (produção)
Variáveis de Ambiente

Exemplo:

APP_NAME=Sistema de Captação de Leads
APP_VERSION=0.1.0
DEBUG=false
ENVIRONMENT=production

API_PREFIX=/api/v1

FIRESTORE_PROJECT_ID=qr-saude-alpha

LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=60
⚠️ Não utilizar em produção
FIRESTORE_EMULATOR_HOST=localhost:8080

O Emulator é apenas para desenvolvimento local.

Dependências

Atualizar:

pip freeze > requirements-prod.txt

ou manter manualmente:

fastapi
uvicorn
google-cloud-firestore
firebase-admin
reportlab
Pillow
qrcode
pydantic
pydantic-settings

Evitar incluir:

pytest
pytest-mock
pytest-cov

no arquivo de produção.

Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements-prod.txt .

RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

CMD exec uvicorn src.main:app \
    --host 0.0.0.0 \
    --port ${PORT}
.dockerignore
venv/
.git/
.pytest_cache/
__pycache__/
.env
node_modules/
firebase-emulator-data/
Testar localmente com Docker

Build:

docker build -t qr-saude-api .

Executar:

docker run -p 8080:8080 qr-saude-api

Swagger:

http://localhost:8080/docs
Primeiro Deploy Manual

Executar:

gcloud run deploy qr-saude-api  --source .  --region southamerica-east1  --allow-unauthenticated
URL de Produção
https://qr-saude-api-533957625089.southamerica-east1.run.app
Consultar Logs

Últimos logs:

gcloud run services logs read qr-saude-api \
  --region=southamerica-east1 \
  --limit=50

Logs em tempo real:

gcloud beta run services logs tail qr-saude-api \
  --region=southamerica-east1
Fazer Novo Deploy

Após alterações:

git add .
git commit -m "descricao"
git push

gcloud run deploy qr-saude-api \
  --source . \
  --region southamerica-east1 \
  --allow-unauthenticated
Configuração Recomendada do Cloud Run

CPU:

1 vCPU

Memória:

512 MB

Instâncias mínimas:

0

Instâncias máximas:

2

Concorrência:

80
CORS

Exemplo:

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://SEU_APP.web.app",
        "https://SEU_APP.firebaseapp.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Durante homologação:

allow_origins=["*"]
Configuração do Frontend
VITE_API_URL=https://qr-saude-api-533957625089.southamerica-east1.run.app

Deploy:

npm run build
firebase deploy
Permissões IAM

A Service Account do Cloud Run deve possuir:

Cloud Datastore User

ou

Cloud Datastore Owner

para o MVP.

Checklist de Produção
Infraestrutura
 Cloud Run criado
 Artifact Registry criado
 Billing ativo
 APIs habilitadas
 Firestore em produção
Backend
 /docs funcionando
 /openapi.json funcionando
 Logs sem erros
 Conexão com Firestore funcionando
 Geração de QR Code funcionando
 Geração de PDF funcionando
Frontend
 Landing Page funcionando
 Dashboard funcionando
 Login funcionando
 Comunicação com API funcionando
Fluxos de Negócio
 Cadastro de parceiros
 Geração de cartões em lote
 Impressão de cartazes
 Registro de leads
 Registro de vendas
 Dashboard de métricas
Recuperação de Erros

Caso um deploy falhe:

Listar revisões:

gcloud run revisions list \
  --service=qr-saude-api \
  --region=southamerica-east1

Voltar para revisão anterior:

gcloud run services update-traffic qr-saude-api \
  --to-revisions REVISION_NAME=100 \
  --region southamerica-east1
Fluxo de Produção
Desenvolvimento
      ↓
Commit
      ↓
Push
      ↓
Build Docker
      ↓
Deploy Cloud Run
      ↓
Smoke Test
      ↓
Homologação Cliente
      ↓
Produção
Próximos Passos (Pós-MVP)
Deploy automático via GitHub Actions ou Cloud Build Trigger
Domínio customizado (api.seudominio.com.br)
Monitoramento e alertas
Ambiente de homologação
Banco de dados separado para staging
Observabilidade (Cloud Monitoring)
Backup automatizado do Firestore