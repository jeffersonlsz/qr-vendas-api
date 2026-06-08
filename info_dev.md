## 🛠️ Desenvolvimento Local

### Pré-requisitos
- Python 3.10+
- Node.js (para Firebase CLI)
- Firebase CLI (`npm install -g firebase-tools`)
- Java JRE (necessário para o Firestore Emulator)

### 1. Configuração do Ambiente
```bash
# Criar ambiente virtual
python -m venv venv
source venv/scripts/activate  # Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Execução com Firestore Emulator (Dados Persistentes)
Para garantir que os dados de teste não sejam perdidos entre reinicializações, utilize os comandos de importação e exportação:

```bash
# Iniciar emuladores com persistência
firebase emulators:start --only firestore --project demo-project --import=./data --export-on-exit 
```

### 3. Execução da API FastAPI
Em um novo terminal, com o ambiente virtual ativado:

```bash
# Rodar servidor de desenvolvimento
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Variáveis de Ambiente (.env)
Certifique-se de que seu arquivo `.env` aponta para o emulador durante o desenvolvimento:
```env
FIRESTORE_EMULATOR_HOST="localhost:8080"
GOOGLE_CLOUD_PROJECT="demo-project"