┌─────────────┐
│  App Mobile │
│  (Expo)     │
└──────┬──────┘
       │ gera receita
       ▼
┌─────────────┐
│  Firestore  │ ◄── Banco de Dados (NoSQL)
│  (Firebase) │
└──────┬──────┘
       │ trigger
       ▼
┌─────────────┐
│Cloud Function│
│  (Node.js)  │
└──────┬──────┘
       │ POST /firebase/sync
       ▼
┌─────────────┐
│   FastAPI   │ ◄── API REST
│  (Python)   │
└──────┬──────┘
       │ append NDJSON
       ▼
┌─────────────┐
│events.jsonl │ ◄── Data Lake (NDJSON)
└──────┬──────┘
       │ pipeline
       ▼
┌─────────────┐
│  LightGBM   │ ◄── Modelo ML
│ LambdaMART  │
└──────┬──────┘
       │ predict
       ▼
┌─────────────┐
│  Streamlit  │ ◄── Dashboard (3 visões)
│  Dashboard  │
└─────────────┘