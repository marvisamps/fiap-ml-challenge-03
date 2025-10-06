from fastapi import FastAPI, HTTPException, Query
from common.schemas import Event, RecResponse, RecItem, RecipeGenerated, RecipeFavorited, FirebaseEvent
from common.config import DATA_EVENTS_PATH, MODEL_PATH, TOP_K, CANDIDATES_TOPN
import json, os, pandas as pd, lightgbm as lgb
from datetime import datetime
from pathlib import Path

app = FastAPI(title="Prato do Dia - Reco API", version="1.0.0")

@app.get("/")
def root():
    return {
        "message": "Prato do Dia - Reco API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "events": "POST /events - Ingestão de eventos genéricos",
            "firebase_sync": "POST /firebase/sync - Sincronização de eventos do Firebase",
            "recipe_generated": "POST /firebase/recipe-generated - Evento de receita gerada",
            "recipe_favorited": "POST /firebase/recipe-favorited - Evento de receita favoritada",
            "recommendations": "GET /recommendations - Recomendações personalizadas"
        }
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": _model is not None,
        "events_file_exists": Path(DATA_EVENTS_PATH).exists()
    }

# lazy load do modelo
_model = None
def get_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise HTTPException(500, "Modelo não encontrado. Treine primeiro.")
        _model = lgb.Booster(model_file=MODEL_PATH)
    return _model

@app.post("/events", status_code=202)
def ingest(ev: Event):
    """Ingestão de eventos genéricos (formato de simulação)"""
    with open(DATA_EVENTS_PATH, "a") as f:
        f.write(json.dumps(ev.model_dump(mode="json")) + "\n")
    return {"status": "accepted"}

@app.post("/firebase/recipe-generated", status_code=202)
def recipe_generated(event: RecipeGenerated):
    """Endpoint para receber eventos de receitas geradas no app"""
    import hashlib
    
    # Gerar recipe_id baseado no nome da receita
    recipe_id = f"rec_{hashlib.md5(event.recipe_name.lower().encode()).hexdigest()[:8]}"
    
    # Converter para formato interno
    internal_event = {
        "event_time": event.created_at.isoformat() + "Z",
        "user_id": event.user_id,
        "event_name": "recipe_generate",
        "recipe_id": recipe_id,
        "recipe_name": event.recipe_name,
        "query": event.query,
        "full_recipe": event.full_recipe,
        "platform": "mobile",
        "source": "app"
    }
    
    # Salvar evento
    with open(DATA_EVENTS_PATH, "a") as f:
        f.write(json.dumps(internal_event) + "\n")
    
    return {
        "status": "accepted",
        "recipe_id": recipe_id,
        "message": "Receita gerada registrada com sucesso"
    }

@app.post("/firebase/recipe-favorited", status_code=202)
def recipe_favorited(event: RecipeFavorited):
    """Endpoint para receber eventos de receitas favoritadas no app"""
    import hashlib
    
    # Gerar recipe_id baseado no nome da receita
    recipe_id = f"rec_{hashlib.md5(event.name.lower().encode()).hexdigest()[:8]}"
    
    # Converter para formato interno
    internal_event = {
        "event_time": event.added_at.isoformat() + "Z",
        "user_id": event.user_id,
        "event_name": "save_recipe",
        "recipe_id": recipe_id,
        "recipe_name": event.name,
        "query": event.query or "",
        "platform": "mobile",
        "source": "app"
    }
    
    # Salvar evento
    with open(DATA_EVENTS_PATH, "a") as f:
        f.write(json.dumps(internal_event) + "\n")
    
    return {
        "status": "accepted",
        "recipe_id": recipe_id,
        "message": "Receita favoritada registrada com sucesso"
    }

@app.post("/firebase/sync", status_code=202)
def firebase_sync(events: list[FirebaseEvent]):
    """
    Sincronização em lote de eventos do Firebase
    Aceita múltiplos eventos de uma vez
    """
    from data.firebase_sync import firebase_to_event
    
    processed = 0
    with open(DATA_EVENTS_PATH, "a") as f:
        for fb_event in events:
            event_dict = {
                "event_type": fb_event.event_type,
                "user_id": fb_event.user_id,
                "timestamp": fb_event.timestamp.isoformat() + "Z",
                "data": fb_event.data
            }
            
            internal_event = firebase_to_event(event_dict)
            if internal_event:
                f.write(json.dumps(internal_event) + "\n")
                processed += 1
    
    return {
        "status": "accepted",
        "processed": processed,
        "total": len(events),
        "message": f"{processed} eventos sincronizados com sucesso"
    }

def load_candidates(user_id: str) -> pd.DataFrame:
    # KISS: usar features de validação como candidatos (em produção: gerar topN por dieta/popularidade/similares)
    from common.config import FEATURES_VAL_PATH
    if not os.path.exists(FEATURES_VAL_PATH):
        raise HTTPException(500, "Gere features primeiro.")
    df = pd.read_parquet(FEATURES_VAL_PATH)
    # pegar subset do usuário; se muito pequeno, usar top por views
    du = df[df.user_id == user_id]
    if du.empty:
        du = df.sort_values("views", ascending=False).head(CANDIDATES_TOPN).copy()
        du["user_id"] = user_id
    return du

@app.get("/recommendations", response_model=RecResponse)
def recommendations(user_id: str, k: int = TOP_K, variant: str = Query("model_v1", enum=["baseline","model_v1"])):
    df = load_candidates(user_id)
    # baseline = ordenar por saves/views/pop
    if variant == "baseline":
        df = df.assign(score=(df["saves"] / (df["views"].clip(lower=1)))).sort_values("score", ascending=False)
    else:
        model = get_model()
        X = df.drop(columns=["user_id","recipe_id","last_ts","label"], errors="ignore")
        df = df.assign(score=model.predict(X)).sort_values("score", ascending=False)

    out = df.head(k)
    items = [RecItem(recipe_id=r.recipe_id, score=float(r.score)) for r in out.itertuples()]
    return RecResponse(user_id=user_id, items=items)

