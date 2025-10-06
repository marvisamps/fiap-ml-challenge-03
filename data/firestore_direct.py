"""
Conexão Direta com Firestore usando Firebase Admin SDK
Permite ler e sincronizar dados diretamente do Firestore
"""
import os
import json
from datetime import datetime
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Dict, Optional
import logging
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FirestoreSync:
    """Cliente para sincronização com Firestore"""
    
    def __init__(self, service_account_path: str = None):
        """
        Inicializa conexão com Firestore
        
        Args:
            service_account_path: Caminho para serviceAccountKey.json
        """
        self.db = None
        self.app = None
        
        # Tentar inicializar
        if service_account_path and Path(service_account_path).exists():
            self._initialize(service_account_path)
        else:
            logger.warning("Service Account Key não encontrado. Configure FIREBASE_SERVICE_ACCOUNT_PATH no .env")
    
    def _initialize(self, service_account_path: str):
        """Inicializa Firebase Admin SDK"""
        try:
            cred = credentials.Certificate(service_account_path)
            self.app = firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            logger.info("✅ Conectado ao Firestore com sucesso!")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao Firestore: {e}")
            raise
    
    def is_connected(self) -> bool:
        """Verifica se está conectado"""
        return self.db is not None
    
    def get_recipes_generated(self, limit: int = None, start_after: datetime = None) -> List[Dict]:
        """
        Busca receitas geradas pelos usuários
        
        Args:
            limit: Número máximo de documentos (None = sem limite)
            start_after: Data para paginação
            
        Returns:
            Lista de receitas
        """
        if not self.is_connected():
            logger.warning("Não conectado ao Firestore")
            return []
        
        try:
            query = self.db.collection('recipes_generated')
            
            if limit:
                query = query.limit(limit)
            
            if start_after:
                query = query.where('createdAt', '>', start_after)
            
            docs = query.stream()
            
            recipes = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                recipes.append(data)
            
            logger.info(f"✅ Buscou {len(recipes)} receitas geradas")
            return recipes
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar receitas: {e}")
            return []
    
    def get_recipes_favorited(self, limit: int = None, start_after: datetime = None) -> List[Dict]:
        """
        Busca receitas favoritadas pelos usuários
        Estrutura: users/{userId}/favoriteLists/{hash}/items/{recipeId}
        
        Args:
            limit: Número máximo de documentos (None = sem limite)
            start_after: Data para paginação
            
        Returns:
            Lista de receitas favoritadas
        """
        if not self.is_connected():
            logger.warning("Não conectado ao Firestore")
            return []
        
        try:
            recipes = []
            count = 0
            
            # Buscar todos os usuários
            users = list(self.db.collection('users').stream())
            logger.info(f"🔍 Processando {len(users)} usuários...")
            
            for idx, user_doc in enumerate(users, 1):
                user_id = user_doc.id
                if idx % 10 == 0:
                    logger.info(f"   Processando usuário {idx}/{len(users)}...")
                
                # Navegar em favoriteLists de cada usuário
                favorite_lists = self.db.collection('users').document(user_id).collection('favoriteLists').stream()
                
                for fav_list in favorite_lists:
                    # Navegar em items de cada favorite list
                    items = self.db.collection('users').document(user_id).collection('favoriteLists').document(fav_list.id).collection('items').stream()
                    
                    for item_doc in items:
                        if limit and count >= limit:
                            break
                        
                        data = item_doc.to_dict()
                        data['id'] = item_doc.id
                        data['user_id'] = user_id  # Adicionar user_id para contexto
                        data['favorite_list_id'] = fav_list.id
                        
                        # Filtrar por data se necessário
                        if start_after and 'addedAt' in data:
                            if data['addedAt'] <= start_after:
                                continue
                        
                        recipes.append(data)
                        count += 1
                    
                    if limit and count >= limit:
                        break
                
                if limit and count >= limit:
                    break
            
            logger.info(f"✅ Buscou {len(recipes)} receitas favoritadas de {len(set(r['user_id'] for r in recipes))} usuários")
            return recipes
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar favoritos: {e}")
            return []
    
    def sync_to_jsonl(self, output_path: str = "data/events.jsonl", batch_size: int = None):
        """
        Sincroniza dados do Firestore para arquivo JSONL
        
        Args:
            output_path: Caminho do arquivo de saída
            batch_size: Tamanho do lote por sincronização (None = sem limite, busca tudo)
        """
        if not self.is_connected():
            logger.error("❌ Não conectado ao Firestore. Configure as credenciais primeiro.")
            return
        
        logger.info("🔄 Iniciando sincronização Firestore → JSONL...")
        
        # Buscar dados (sem limite = pega tudo)
        generated = self.get_recipes_generated(limit=batch_size)
        favorited = self.get_recipes_favorited(limit=batch_size)
        
        # Converter para eventos
        events = []
        
        for recipe in generated:
            # Formatar data corretamente (remover +00:00 e adicionar Z)
            created_at = recipe.get('createdAt', datetime.now())
            if hasattr(created_at, 'isoformat'):
                event_time = created_at.isoformat().replace('+00:00', 'Z')
            else:
                event_time = datetime.now().isoformat() + "Z"
            
            event = {
                "event_time": event_time,
                "user_id": recipe.get('userId', 'unknown'),
                "event_name": "recipe_generate",
                "recipe_id": self._generate_recipe_id(recipe.get('recipeName', '')),
                "recipe_name": recipe.get('recipeName'),
                "query": recipe.get('query', ''),
                "full_recipe": recipe.get('fullRecipe', ''),
                "platform": "mobile",
                "source": "firestore_sync"
            }
            events.append(event)
        
        for recipe in favorited:
            # Formatar data corretamente (remover +00:00 e adicionar Z)
            added_at = recipe.get('addedAt', datetime.now())
            if hasattr(added_at, 'isoformat'):
                event_time = added_at.isoformat().replace('+00:00', 'Z')
            else:
                event_time = datetime.now().isoformat() + "Z"
            
            event = {
                "event_time": event_time,
                "user_id": recipe.get('user_id', 'unknown'),  # user_id já foi extraído do path
                "event_name": "save_recipe",
                "recipe_id": self._generate_recipe_id(recipe.get('name', '')),
                "recipe_name": recipe.get('name'),
                "query": recipe.get('query', ''),
                "platform": "mobile",
                "source": "firestore_sync"
            }
            events.append(event)
        
        # Salvar no arquivo
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'a') as f:
            for event in events:
                f.write(json.dumps(event) + "\n")
        
        logger.info(f"✅ Sincronizado {len(events)} eventos para {output_path}")
        return len(events)
    
    def _generate_recipe_id(self, recipe_name: str) -> str:
        """Gera ID único para receita"""
        import hashlib
        return f"rec_{hashlib.md5(recipe_name.lower().encode()).hexdigest()[:8]}"
    
    def listen_realtime(self, callback):
        """
        Escuta mudanças em tempo real no Firestore
        
        Args:
            callback: Função a ser chamada quando houver mudança
        """
        if not self.is_connected():
            logger.error("❌ Não conectado ao Firestore")
            return
        
        logger.info("👂 Escutando mudanças em tempo real no Firestore...")
        
        # Listener para receitas geradas
        def on_generated_snapshot(col_snapshot, changes, read_time):
            for change in changes:
                if change.type.name == 'ADDED':
                    doc = change.document.to_dict()
                    doc['event_type'] = 'recipe_generate'
                    doc['id'] = change.document.id
                    callback(doc)
        
        # Registrar listener para receitas geradas
        self.db.collection('recipes_generated').on_snapshot(on_generated_snapshot)
        logger.info("✅ Listener para recipes_generated registrado!")
        
        # Para favoritos, precisamos escutar collection groups
        # Isso escuta todos os documentos em qualquer coleção "items"
        try:
            def on_favorite_items_snapshot(col_snapshot, changes, read_time):
                for change in changes:
                    if change.type.name == 'ADDED':
                        doc = change.document.to_dict()
                        doc['event_type'] = 'save_recipe'
                        doc['id'] = change.document.id
                        # Extrair user_id do path: users/{userId}/favoriteLists/{hash}/items/{recipeId}
                        path_parts = change.document.reference.path.split('/')
                        if len(path_parts) >= 2 and path_parts[0] == 'users':
                            doc['user_id'] = path_parts[1]
                        callback(doc)
            
            # Escutar collection group "items" (todas as coleções chamadas "items" em qualquer nível)
            self.db.collection_group('items').on_snapshot(on_favorite_items_snapshot)
            logger.info("✅ Listener para favoritos (collection group 'items') registrado!")
            
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível registrar listener para favoritos: {e}")
            logger.info("💡 Dica: Você pode precisar criar um índice no Firestore Console")
        
        logger.info("✅ Todos os listeners registrados!")


# ============== FUNÇÕES UTILITÁRIAS ==============

def sync_once(service_account_path: str = None):
    """Executa sincronização única"""
    if not service_account_path:
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
    
    if not service_account_path or not Path(service_account_path).exists():
        logger.error("❌ Service Account Key não encontrado!")
        logger.info("Configure FIREBASE_SERVICE_ACCOUNT_PATH no .env")
        return
    
    sync = FirestoreSync(service_account_path)
    count = sync.sync_to_jsonl()
    logger.info(f"🎉 Sincronização completa! {count} eventos processados.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        service_account = sys.argv[1]
    else:
        service_account = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'serviceAccountKey.json')
    
    sync_once(service_account)

