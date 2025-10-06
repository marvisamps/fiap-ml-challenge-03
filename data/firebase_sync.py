"""
Script de sincronização Firebase → Sistema de Recomendação
Extrai dados do Firebase e converte para o formato de eventos NDJSON
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import hashlib


def generate_recipe_id(recipe_name: str, user_id: str) -> str:
    """Gera um ID único para a receita baseado no nome e usuário"""
    unique_str = f"{recipe_name}_{user_id}".lower()
    return f"rec_{hashlib.md5(unique_str.encode()).hexdigest()[:8]}"


def firebase_to_event(firebase_data: Dict) -> Dict:
    """
    Converte dados do Firebase para o formato de evento NDJSON
    
    Args:
        firebase_data: Dicionário com dados do Firebase
        
    Returns:
        Evento no formato NDJSON
    """
    event_type = firebase_data.get("event_type")
    
    if event_type == "recipe_generate":
        # Receita gerada pelo usuário
        data = firebase_data.get("data", {})
        recipe_id = generate_recipe_id(
            data.get("recipeName", ""),
            firebase_data.get("user_id", "")
        )
        
        return {
            "event_time": firebase_data["timestamp"],
            "user_id": firebase_data["user_id"],
            "event_name": "recipe_generate",
            "recipe_id": recipe_id,
            "recipe_name": data.get("recipeName"),
            "query": data.get("query", ""),
            "full_recipe": data.get("fullRecipe", ""),
            "platform": "mobile",
            "source": "app"
        }
    
    elif event_type == "save_recipe":
        # Receita favoritada
        data = firebase_data.get("data", {})
        recipe_id = generate_recipe_id(
            data.get("name", ""),
            firebase_data.get("user_id", "")
        )
        
        return {
            "event_time": firebase_data["timestamp"],
            "user_id": firebase_data["user_id"],
            "event_name": "save_recipe",
            "recipe_id": recipe_id,
            "recipe_name": data.get("name"),
            "query": data.get("query", ""),
            "platform": "mobile",
            "source": "app"
        }
    
    return None


def sync_firebase_to_jsonl(firebase_events: List[Dict], output_path: str = "data/events.jsonl"):
    """
    Sincroniza eventos do Firebase para o arquivo JSONL
    
    Args:
        firebase_events: Lista de eventos do Firebase
        output_path: Caminho do arquivo de saída
    """
    output_file = Path(output_path)
    
    # Ler eventos existentes (se houver)
    existing_events = []
    if output_file.exists():
        with open(output_file, 'r') as f:
            existing_events = [json.loads(line) for line in f]
    
    # Converter novos eventos
    new_events = []
    for fb_event in firebase_events:
        event = firebase_to_event(fb_event)
        if event:
            new_events.append(event)
    
    # Combinar e remover duplicatas (baseado em user_id + recipe_id + event_time)
    all_events = existing_events + new_events
    unique_events = {}
    for event in all_events:
        key = f"{event['user_id']}_{event.get('recipe_id', 'none')}_{event['event_time']}"
        unique_events[key] = event
    
    # Escrever de volta
    with open(output_file, 'w') as f:
        for event in unique_events.values():
            f.write(json.dumps(event) + "\n")
    
    print(f"✅ Sincronizado: {len(new_events)} novos eventos")
    print(f"📊 Total de eventos: {len(unique_events)}")
    print(f"💾 Salvo em: {output_path}")


def example_usage():
    """Exemplo de uso com dados mock do Firebase"""
    
    # Simular dados vindos do Firebase
    firebase_events = [
        {
            "event_type": "recipe_generate",
            "user_id": "AqT3Xs5GG1alMiISapguf3Wg2Vi2",
            "timestamp": "2025-10-05T13:41:28Z",
            "data": {
                "recipeName": "Sanduíche Integral de Abacate e Frango Grelhado",
                "query": "Lanche saudável com pão integral",
                "fullRecipe": "**Nome da Receita:** Sanduíche Integral...",
                "calories": None,
                "imageUrl": None,
                "preparationTime": None
            }
        },
        {
            "event_type": "save_recipe",
            "user_id": "AqT3Xs5GG1alMiISapguf3Wg2Vi2",
            "timestamp": "2025-10-05T15:59:22Z",
            "data": {
                "name": "Batatas Rústicas com Carne ao Molho Especial",
                "response": "**Nome da Receita:** Batatas Rústicas...",
                "query": "",
                "imageUrl": None
            }
        }
    ]
    
    # Sincronizar
    sync_firebase_to_jsonl(firebase_events)


if __name__ == "__main__":
    print("🔄 Firebase Sync - Sistema de Recomendação")
    print("=" * 50)
    example_usage()


