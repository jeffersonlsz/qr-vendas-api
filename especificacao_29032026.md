# 📘 Especificação Técnica — Sistema de Captação via QR Code para Vendas de Planos de Saúde

## 1. 📌 Visão Geral

Este sistema tem como objetivo permitir a captação de leads através de QR Codes distribuídos em veículos de motoristas parceiros (ex: Uber), com rastreamento completo da origem do lead e atribuição de comissão por venda.

O sistema funciona como uma plataforma de **tracking de afiliados offline → online**, conectando:

* Parceiros (motoristas)
* Leads (clientes interessados)
* Vendedores (fechamento de vendas)

---

## 2. 🎯 Objetivos do Sistema

* Gerar leads qualificados via QR Code
* Rastrear origem de cada lead
* Permitir gestão de parceiros (Ubers)
* Calcular comissões automaticamente
* Fornecer dashboards distintos por perfil
* Permitir evolução futura para motor de afiliados escalável

---

## 3. 🧱 Arquitetura Geral

### 3.1 Frontend

* Framework: Vue.js
* Hosting: Firebase Hosting
* Responsabilidades:

  * Landing page (captação)
  * Dashboard parceiro
  * Dashboard admin/vendedor

---

### 3.2 Backend

* Framework: FastAPI
* Deploy: Google Cloud Run
* Responsabilidades:

  * API REST
  * Regras de negócio
  * Tracking de leads
  * Registro de vendas
  * Cálculo de comissão

---

### 3.3 Banco de Dados

* Serviço: Firebase Firestore
* Tipo: NoSQL (document-based)

---

### 3.4 Autenticação

* Firebase Authentication
* Perfis:

  * admin
  * parceiro

---

## 4. 🔗 Estrutura de URLs e Tracking

### 4.1 URL Base de Captação

```
https://seudominio.com/lp?ref=UBER_123
```

### 4.2 Parâmetro de Tracking

* `ref`: identificador único do parceiro

---

### 4.3 Persistência do Tracking

Ao acessar a landing page:

* Salvar `ref` em:

  * localStorage (principal)
  * fallback: cookie

```js
localStorage.setItem("ref_parceiro", ref)
```

---

## 5. 🧩 Modelagem de Dados (Firestore)

---

### 5.1 Coleção: `parceiros`

```json
{
  "id": "UBER_123",
  "nome": "Carlos Silva",
  "telefone": "+559999999999",
  "ativo": true,
  "percentual_comissao": 0.1,
  "created_at": "timestamp"
}
```

---

### 5.2 Coleção: `leads`

```json
{
  "id": "lead_001",
  "parceiro_id": "UBER_123",
  "nome": "João",
  "telefone": "+559888888888",
  "origem": "qr_code",
  "status": "novo",
  "created_at": "timestamp"
}
```

Status possíveis:

* `novo`
* `em_atendimento`
* `convertido`
* `perdido`

---

### 5.3 Coleção: `vendas`

```json
{
  "id": "venda_001",
  "lead_id": "lead_001",
  "parceiro_id": "UBER_123",
  "valor_venda": 1200,
  "percentual_comissao": 0.1,
  "comissao": 120,
  "status": "pendente",
  "created_at": "timestamp"
}
```

Status possíveis:

* `pendente`
* `pago`

---

## 6. ⚙️ Regras de Negócio

---

### 6.1 Criação de Lead

Um lead deve ser criado quando:

* Usuário preenche formulário OU
* Usuário clica no WhatsApp (modo simplificado)

---

### 6.2 Associação de Parceiro

* O sistema deve capturar `ref`
* Validar existência do parceiro
* Associar automaticamente ao lead

---

### 6.3 Conversão em Venda

* Apenas leads existentes podem gerar vendas
* Venda deve herdar:

  * parceiro_id
  * percentual_comissao

---

### 6.4 Cálculo de Comissão

```python
comissao = valor_venda * percentual_comissao
```

---

### 6.5 Visibilidade de Dados

#### Parceiro:

* Apenas seus leads
* Apenas suas vendas
* Comissão total

#### Admin:

* Todos os dados
* Visão agregada

---

## 7. 🔌 API — Endpoints (FastAPI)

---

### 7.1 Parceiros

#### Criar parceiro

```
POST /parceiros
```

#### Listar parceiros

```
GET /parceiros
```

---

### 7.2 Leads

#### Criar lead

```
POST /leads
```

Body:

```json
{
  "nome": "João",
  "telefone": "+559888888888",
  "parceiro_id": "UBER_123"
}
```

---

#### Listar leads

```
GET /leads
```

Filtros:

* parceiro_id
* status

---

### 7.3 Vendas

#### Criar venda

```
POST /vendas
```

Body:

```json
{
  "lead_id": "lead_001",
  "valor_venda": 1200
}
```

---

#### Listar vendas

```
GET /vendas
```

---

### 7.4 Dashboard

#### Resumo do parceiro

```
GET /parceiros/{id}/resumo
```

Retorno:

```json
{
  "total_leads": 10,
  "total_vendas": 3,
  "total_comissao": 300
}
```

---

## 8. 📱 Frontend

---

### 8.1 Landing Page

Componentes:

* Headline
* CTA (WhatsApp)
* Formulário (fase 2)

---

### 8.2 Fluxo WhatsApp

Link dinâmico:

```
https://wa.me/55XXXXXXXXXX?text=Vim%20pelo%20QR%20ID%20UBER_123
```

---

### 8.3 Dashboard Parceiro

* Leads gerados
* Vendas realizadas
* Comissão acumulada

---

### 8.4 Dashboard Admin

* Lista completa de leads
* Conversões
* Performance por parceiro

---

## 9. 🔐 Segurança

* Firebase Auth obrigatório para dashboards
* Validação de roles no backend
* Proteção de endpoints por token

---

## 10. 📊 Métricas Importantes

* Leads por parceiro
* Taxa de conversão
* Receita por parceiro
* Comissão total

---

## 11. 🚀 Roadmap de Evolução

---

### Fase 1 (MVP)

* QR Code com ref
* Landing simples
* WhatsApp tracking

---

### Fase 2

* Formulário estruturado
* Persistência de leads

---

### Fase 3

* Dashboard completo
* Registro manual de vendas

---

### Fase 4

* Automação de comissões
* Gamificação de parceiros

---

### Fase 5 (Avançado)

* IA para qualificação de leads
* Ranking de parceiros
* Integração com CRM

---

## 12. ⚠️ Considerações Técnicas

* Evitar dependência exclusiva de WhatsApp tracking
* Sempre persistir `ref`
* Garantir idempotência nos endpoints
* Usar timestamps consistentes (UTC)

---

## 13. 🧠 Conceito Central

Este sistema deve ser tratado como:

> Um motor de aquisição offline com rastreamento digital e monetização baseada em performance.

---

## 14. 📌 Observações Finais

* Priorizar simplicidade no MVP
* Validar o modelo com poucos parceiros antes de escalar
* Evitar overengineering nas primeiras versões
* Garantir coleta de dados desde o início

---
