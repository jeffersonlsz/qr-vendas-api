import random
from datetime import datetime
from google.cloud import firestore
import os

# 🔥 apontar pro emulator
os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"

db = firestore.Client(project="demo-project")

# 📛 Listas de nomes
PRIMEIROS_NOMES = [
    "João", "Marcio", "Bruno", "Carlos", "Felipe",
    "Lucas", "Rafael", "André", "Fernando", "Gustavo",
    "Pedro", "Ricardo", "Thiago", "Daniel", "Eduardo"
]

SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Pereira",
    "Costa", "Rodrigues", "Almeida", "Nascimento", "Lima",
    "Araújo", "Fernandes", "Carvalho", "Gomes", "Martins"
]

def gerar_nome():
    return f"{random.choice(PRIMEIROS_NOMES)} {random.choice(SOBRENOMES)}"

def gerar_parceiros(qtd=10):
    parceiros_ref = db.collection("parceiros")

    for i in range(1, qtd + 1):
        parceiro_id = f"UBER_{i:03d}"

        parceiro = {
            "id": parceiro_id,
            "nome": gerar_nome(),
            "telefone": f"+5561999{random.randint(100000, 999999)}",
            "percentual_comissao": round(random.uniform(0.05, 0.15), 2),
            "ativo": True,
            "created_at": datetime.utcnow()
        }

        parceiros_ref.document(parceiro_id).set(parceiro)

        print(f"✅ Criado: {parceiro_id} - {parceiro['nome']}")

if __name__ == "__main__":
    gerar_parceiros(10)
    print("\n🚀 Seed finalizado!")