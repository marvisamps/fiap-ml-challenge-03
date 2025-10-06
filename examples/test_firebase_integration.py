"""
Script de teste para integração Firebase
Envia eventos de teste para a API
"""
import requests
import json
from datetime import datetime
import sys

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000"

def test_recipe_generated():
    """Testa endpoint de receita gerada"""
    print("\n[TEST] Testando: Receita Gerada")
    print("=" * 50)
    
    payload = {
        "recipeName": "Salada Caesar Vegetariana",
        "query": "Salada leve e saudável vegetariana",
        "fullRecipe": """**Nome da Receita:** Salada Caesar Vegetariana
        
**Ingredientes:**
• 1 pé de alface romana
• 50g de parmesão ralado
• Croutons integrais
• Molho Caesar vegano
• Limão siciliano

**Modo de Preparo:**
1. Lave e corte a alface
2. Adicione o parmesão e croutons
3. Regue com molho Caesar
4. Finalize com limão

**Informação Nutricional:**
• Calorias: 250 kcal
• Proteínas: 12g
• Carboidratos: 25g
        """,
        "userId": "test_user_001",
        "createdAt": datetime.now().isoformat() + "Z",
        "calories": 250,
        "preparationTime": 15
    }
    
    response = requests.post(
        f"{API_URL}/firebase/recipe-generated",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 202


def test_recipe_favorited():
    """Testa endpoint de receita favoritada"""
    print("\n[TEST] Testando: Receita Favoritada")
    print("=" * 50)
    
    payload = {
        "name": "Wrap de Frango com Legumes",
        "response": """**Nome da Receita:** Wrap de Frango com Legumes
        
Um wrap delicioso e nutritivo com frango grelhado e vegetais frescos.
        
**Ingredientes:**
• Tortilha integral
• 200g de frango
• Alface, tomate, cenoura
• Molho de iogurte
        """,
        "addedAt": datetime.now().isoformat() + "Z",
        "userId": "test_user_002",
        "query": "wrap saudável",
        "imageUrl": None
    }
    
    response = requests.post(
        f"{API_URL}/firebase/recipe-favorited",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 202


def test_batch_sync():
    """Testa sincronização em lote"""
    print("\n[TEST] Testando: Sincronizacao em Lote")
    print("=" * 50)
    
    payload = [
        {
            "event_type": "recipe_generate",
            "user_id": "batch_user_001",
            "timestamp": datetime.now().isoformat() + "Z",
            "data": {
                "recipeName": "Smoothie de Morango",
                "query": "smoothie frutas",
                "fullRecipe": "Bata morangos, banana e iogurte..."
            }
        },
        {
            "event_type": "save_recipe",
            "user_id": "batch_user_002",
            "timestamp": datetime.now().isoformat() + "Z",
            "data": {
                "name": "Panqueca de Aveia",
                "response": "Misture aveia, ovos e banana..."
            }
        }
    ]
    
    response = requests.post(
        f"{API_URL}/firebase/sync",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 202


def test_health():
    """Testa health check"""
    print("\n[TEST] Testando: Health Check")
    print("=" * 50)
    
    response = requests.get(f"{API_URL}/health")
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


if __name__ == "__main__":
    print("\n=== TESTE DE INTEGRACAO FIREBASE ===")
    print("=" * 50)
    print(f"API URL: {API_URL}")
    print("=" * 50)
    
    try:
        # Executar testes
        results = {
            "Health Check": test_health(),
            "Recipe Generated": test_recipe_generated(),
            "Recipe Favorited": test_recipe_favorited(),
            "Batch Sync": test_batch_sync()
        }
        
        # Resumo
        print("\n" + "=" * 50)
        print("=== RESUMO DOS TESTES ===")
        print("=" * 50)
        
        for test_name, passed in results.items():
            status = "[OK] PASSOU" if passed else "[FALHOU]"
            print(f"{test_name:.<40} {status}")
        
        all_passed = all(results.values())
        print("\n" + "=" * 50)
        if all_passed:
            print("[SUCCESS] TODOS OS TESTES PASSARAM!")
            print("\nProximos passos:")
            print("1. Acesse http://localhost:8501")
            print("2. Va para a aba 'Receitas do App'")
            print("3. Veja as receitas de teste que acabaram de ser enviadas")
        else:
            print("[WARNING] ALGUNS TESTES FALHARAM")
            print("Verifique se a API esta rodando: python -m uvicorn api.main:app")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Nao foi possivel conectar a API")
        print("Certifique-se de que a API esta rodando:")
        print("  uvicorn api.main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n[ERROR] {e}")

