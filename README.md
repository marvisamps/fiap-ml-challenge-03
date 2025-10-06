# 🍽️ Prato do Dia - Sistema de Recomendação — Fase 3

> Sistema de recomendação de receitas com Machine Learning (KISS/YAGNI/DRY)

## 🚀 Stack Tecnológica
- **API**: FastAPI, Pydantic
- **ML**: LightGBM (LambdaMART), scikit-learn
- **Data**: Pandas, Parquet, NDJSON
- **Dashboard**: Streamlit, Plotly
- **Deploy**: Docker

## 📦 Instalação

```bash
# 1. Clonar repositório
git clone <repo-url>
cd recipe-recommender

# 2. Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp env.example .env  # Ajuste se necessário
# Ou criar manualmente com os valores em env.example
```

## 🎯 Execução Rápida (Windows - Recomendado)

### Menu Interativo

```powershell
.\start.ps1
```

**Opções disponíveis:**
- `[1]` 📊 Dashboard (Streamlit)
- `[2]` 🚀 API (FastAPI)
- `[3]` 🔄 Sincronizar Firebase
- `[4]` ⚙️  Gerar Features
- `[5]` 🤖 Treinar Modelo
- `[6]` 🔍 Verificar Ambiente
- `[7]` 📤 Commit e Push
- `[8]` 🎬 Pipeline Completo

### Scripts Individuais

```powershell
# Executar Dashboard (resolve PYTHONPATH automaticamente)
.\run-dashboard.ps1

# Executar API
.\run-api.ps1

# Verificar tudo antes de apresentar
.\pre-apresentacao-checklist.ps1

# Commit e push automático
.\commit-and-push.ps1
```

---

## 🐧 Execução Manual (Linux/Mac ou Detalhado)

⚠️ **Importante:** Sempre defina `PYTHONPATH=.` antes de executar scripts Python

```bash
# 1. Gerar dados simulados (20k eventos) - OU sincronizar Firebase
PYTHONPATH=. python data/simulate.py
# PYTHONPATH=. python data/firestore_direct.py

# 2. Extrair features (User×Recipe)
PYTHONPATH=. python pipelines/features.py

# 3. Treinar modelo LambdaMART
PYTHONPATH=. python models/train.py

# 4. Iniciar API (porta 8000)
PYTHONPATH=. uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Iniciar Dashboard (porta 8501)
PYTHONPATH=. streamlit run dash/app.py
```

## 🌐 Acessar Aplicação

- **API Docs (Swagger)**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501
- **Health Check**: http://localhost:8000/health

## 📊 Dashboard (3 Abas)

### 1️⃣ Visão Executiva
Para gestores e stakeholders:
- Métricas de negócio (usuários, receitas, conversão)
- Top 10 receitas populares
- Gráficos de engajamento
- Insights acionáveis

### 2️⃣ Visão Técnica
Para Data Scientists:
- Distribuições de features
- Matriz de correlação
- Estatísticas descritivas
- Dados brutos (parquet)

### 3️⃣ Receitas do App
Visualização de dados reais do Firebase:
- Receitas geradas pelos usuários
- Receitas favoritadas
- Filtros por tipo e usuário
- Top buscas e usuários ativos

## 🔥 Integração Firebase

### 📋 3 Modos de Sincronização

#### 1. **Tempo Real** (Desenvolvimento)
```bash
python data/firestore_realtime.py
```
Ouve mudanças instantaneamente no Firestore.

#### 2. **Agendado** (Produção Local)
```bash
python data/firestore_scheduler.py
```
Sincroniza a cada X minutos (configurável).

#### 3. **Manual** (Sob Demanda)
```bash
python data/firestore_direct.py
```
Execute quando precisar sincronizar.

### ☁️ Cloud Functions (Produção)

Deploy de functions que sincronizam automaticamente:

```bash
cd cloud_functions
firebase deploy --only functions
```

**Funções disponíveis:**
- `onRecipeGenerated` - Trigger quando receita é gerada
- `onRecipeFavorited` - Trigger quando receita é favoritada
- `syncManual` - HTTP function para sync manual
- `syncScheduled` - Sync agendado (5 em 5 min)

### 🌐 Endpoints da API

#### 1. Receita Gerada
```bash
POST /firebase/recipe-generated
Content-Type: application/json

{
  "recipeName": "Salada Caesar",
  "query": "salada leve",
  "fullRecipe": "...",
  "userId": "user123",
  "createdAt": "2025-10-05T18:00:00Z"
}
```

#### 2. Receita Favoritada
```bash
POST /firebase/recipe-favorited
Content-Type: application/json

{
  "name": "Wrap de Frango",
  "response": "...",
  "addedAt": "2025-10-05T18:00:00Z",
  "userId": "user123"
}
```

#### 3. Sincronização em Lote
```bash
POST /firebase/sync
Content-Type: application/json

[
  { "event_type": "recipe_generate", ... },
  { "event_type": "save_recipe", ... }
]
```

### 🧪 Testar Integração

```bash
python examples/test_firebase_integration.py
```

**Resultado esperado: 4/4 testes passando** ✅

### 📚 Documentação Completa

- **[QUICKSTART.md](QUICKSTART.md)** - Comece em 5 minutos ⚡
- **[SETUP_LOCAL.md](SETUP_LOCAL.md)** - Configuração local completa (20 min)
- **[FIREBASE_INTEGRATION.md](FIREBASE_INTEGRATION.md)** - Detalhes Firebase (15 min)
- **[FIRESTORE_STRUCTURE.md](FIRESTORE_STRUCTURE.md)** - Estrutura do Firestore (collections, queries, índices)
- **[FIRESTORE_SETUP_CHECKLIST.md](FIRESTORE_SETUP_CHECKLIST.md)** ✅ - Checklist de setup do Firestore
- **[docs/MODEL_EVALUATION.md](docs/MODEL_EVALUATION.md)** 🤖 - Avaliação do modelo (NDCG, LambdaMART)
- **[docs/PRESENTATION_GUIDE.md](docs/PRESENTATION_GUIDE.md)** 🎬 - Guia de apresentação (5 min)
- **[SETUP_PRODUCTION.md](SETUP_PRODUCTION.md)** - Deploy em produção (30 min)
- **[cloud_functions/README.md](cloud_functions/README.md)** - Cloud Functions

## 🤖 Modelo de ML

**Algoritmo**: LightGBM LambdaMART (Learning to Rank)  
**Métrica**: NDCG@10 (padrão da indústria para ranking)  
**Features**: views, saves, conversion rate  

**Performance** (dados reais - 501 eventos, 161 usuários):
- **Baseline** (popularidade): NDCG@10 = 0.535
- **Modelo ML** (personalizado): NDCG@10 = 0.583
- **Melhoria: +9% (+0.048 pontos)** 🎯

**Por que garante melhoria?**
- ✅ NDCG@10 = métrica padrão (Netflix, Spotify, Amazon)
- ✅ Split temporal rigoroso (últimos 2 dias = validação)
- ✅ Significância estatística (intervalos de confiança não se sobrepõem)
- ✅ LambdaMART otimiza ordem diretamente (não score absoluto)

**Por que LightGBM LambdaMART?**
- ⚡ **10-20x mais rápido** que XGBoost
- 🎯 **Precisão comparável** ou melhor
- 🧠 **Otimiza NDCG diretamente** (learning to rank)
- 🏭 **Produção-ready** (Microsoft, Kaggle)

📖 **Documentação completa:** [docs/MODEL_EVALUATION.md](docs/MODEL_EVALUATION.md)

## 🐳 Docker

```bash
# Build
docker build -t prato-reco:0.1 .

# Run
docker run -p 8080:8080 --env-file .env prato-reco:0.1
```

## 📁 Estrutura do Projeto

```
recipe-recommender/
├─ README.md                      # Visão geral (este arquivo)
├─ QUICKSTART.md                  # ⚡ Comece em 5 minutos
├─ SETUP_LOCAL.md                 # 🏠 Guia completo local
├─ SETUP_PRODUCTION.md            # 🚀 Deploy em produção
├─ FIREBASE_INTEGRATION.md        # 🔥 Integração Firebase
├─ requirements.txt               # Dependências Python
├─ Dockerfile                     # Container Docker
├─ env.example                    # Exemplo de .env
├─ .gitignore                     # Git ignore
│
├─ common/                        # Código compartilhado
│  ├─ config.py                  # Configurações
│  └─ schemas.py                 # Schemas Pydantic (Firebase)
│
├─ api/                           # API REST
│  └─ main.py                    # FastAPI (6 endpoints)
│
├─ pipelines/                     # Pipelines ML
│  └─ features.py                # Feature engineering
│
├─ models/                        # Modelos ML
│  └─ train.py                   # LambdaMART + NDCG@10
│
├─ dash/                          # Dashboard
│  └─ app.py                     # Streamlit (3 abas)
│
├─ data/                          # Scripts de dados
│  ├─ simulate.py                # Gerador de eventos
│  ├─ firebase_sync.py           # Sync manual
│  ├─ firestore_direct.py        # Conexão direta Firestore
│  ├─ firestore_realtime.py      # 👂 Listener tempo real
│  └─ firestore_scheduler.py     # ⏰ Agendador periódico
│
├─ cloud_functions/               # ☁️ Firebase Functions
│  ├─ functions/
│  │  ├─ index.js                # 4 functions
│  │  └─ package.json
│  ├─ firebase.json
│  └─ README.md                  # Docs Cloud Functions
│
├─ examples/                      # Exemplos e testes
│  └─ test_firebase_integration.py  # Suite de testes
│
└─ artifacts/                     # Artefatos gerados
   └─ model.txt                  # Modelo LightGBM
```

## 🔄 Pipeline de Dados

```
Firebase/App → API → events.jsonl → features.parquet → LightGBM → Recomendações
```

## 🧪 Testar Recomendações

```bash
# Obter recomendações (modelo ML)
curl "http://localhost:8000/recommendations?user_id=USER_ID&k=5&variant=model_v1"

# Obter recomendações (baseline)
curl "http://localhost:8000/recommendations?user_id=USER_ID&k=5&variant=baseline"
```

## 📈 Retreinamento

Para retreinar o modelo com novos dados:

```bash
python pipelines/features.py  # Atualiza features
python models/train.py        # Retreina modelo
```

Sugestão: agendar via cron job (diário/semanal)

## 🎨 Princípios de Design

- **KISS** (Keep It Simple, Stupid): Código simples e direto
- **YAGNI** (You Aren't Gonna Need It): Só o essencial
- **DRY** (Don't Repeat Yourself): Config centralizado

## 📝 TODO

- [ ] Implementar retreinamento automático
- [ ] Adicionar métricas de CTR do app
- [ ] Integrar com BigQuery (futuro)
- [ ] A/B testing dashboard
- [ ] CI/CD pipeline

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua feature branch
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

MIT License

---

Feito com ❤️ para o projeto Prato do Dia

