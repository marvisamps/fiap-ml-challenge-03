"""
Serviço de Sincronização em Tempo Real com Firestore
Roda continuamente ouvindo mudanças e enviando para o sistema
"""
import os
import sys
import time
import signal
import logging
from pathlib import Path
from data.firestore_direct import FirestoreSync
from datetime import datetime
import json
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuração
API_URL = os.getenv('API_URL', 'http://localhost:8000')
SERVICE_ACCOUNT_PATH = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'serviceAccountKey.json')
EVENTS_PATH = os.getenv('DATA_EVENTS_PATH', 'data/events.jsonl')

# Controle de shutdown gracioso
shutdown_flag = False

def signal_handler(sig, frame):
    """Handler para shutdown gracioso"""
    global shutdown_flag
    logger.info("🛑 Recebido sinal de parada. Encerrando...")
    shutdown_flag = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class RealtimeSync:
    """Sincronização em tempo real com Firestore"""
    
    def __init__(self, service_account_path: str):
        self.sync = FirestoreSync(service_account_path)
        self.processed_count = 0
        self.error_count = 0
    
    def process_event(self, doc: dict):
        """
        Processa evento recebido do Firestore
        
        Args:
            doc: Documento do Firestore
        """
        try:
            event_type = doc.get('event_type')
            
            # Converter para formato interno
            if event_type == 'recipe_generate':
                event = {
                    "event_time": doc.get('createdAt', datetime.now()).isoformat() + "Z",
                    "user_id": doc.get('userId', 'unknown'),
                    "event_name": "recipe_generate",
                    "recipe_id": self._generate_recipe_id(doc.get('recipeName', '')),
                    "recipe_name": doc.get('recipeName'),
                    "query": doc.get('query', ''),
                    "full_recipe": doc.get('fullRecipe', ''),
                    "platform": "mobile",
                    "source": "firestore_realtime"
                }
            elif event_type == 'save_recipe':
                event = {
                    "event_time": doc.get('addedAt', datetime.now()).isoformat() + "Z",
                    "user_id": doc.get('userId', 'unknown'),
                    "event_name": "save_recipe",
                    "recipe_id": self._generate_recipe_id(doc.get('name', '')),
                    "recipe_name": doc.get('name'),
                    "query": doc.get('query', ''),
                    "platform": "mobile",
                    "source": "firestore_realtime"
                }
            else:
                logger.warning(f"⚠️ Tipo de evento desconhecido: {event_type}")
                return
            
            # Salvar no arquivo JSONL
            self._save_to_jsonl(event)
            
            # Tentar enviar para API (opcional)
            self._send_to_api(event)
            
            self.processed_count += 1
            logger.info(f"✅ Evento processado: {event['recipe_name'][:50]}... (Total: {self.processed_count})")
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"❌ Erro ao processar evento: {e}")
    
    def _save_to_jsonl(self, event: dict):
        """Salva evento no arquivo JSONL"""
        Path(EVENTS_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(EVENTS_PATH, 'a') as f:
            f.write(json.dumps(event) + "\n")
    
    def _send_to_api(self, event: dict):
        """Envia evento para a API (opcional)"""
        try:
            endpoint = f"{API_URL}/events"
            response = requests.post(endpoint, json=event, timeout=5)
            if response.status_code != 202:
                logger.warning(f"⚠️ API retornou: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.debug(f"API não disponível: {e}")
    
    def _generate_recipe_id(self, recipe_name: str) -> str:
        """Gera ID único para receita"""
        import hashlib
        return f"rec_{hashlib.md5(recipe_name.lower().encode()).hexdigest()[:8]}"
    
    def start(self):
        """Inicia serviço de sincronização em tempo real"""
        if not self.sync.is_connected():
            logger.error("❌ Não foi possível conectar ao Firestore!")
            logger.info("Verifique se o serviceAccountKey.json está configurado corretamente")
            sys.exit(1)
        
        logger.info("=" * 60)
        logger.info("🔥 SERVIÇO DE SINCRONIZAÇÃO EM TEMPO REAL")
        logger.info("=" * 60)
        logger.info(f"📡 Firestore: Conectado")
        logger.info(f"💾 Destino: {EVENTS_PATH}")
        logger.info(f"🌐 API: {API_URL}")
        logger.info("=" * 60)
        logger.info("👂 Aguardando eventos do Firestore...")
        logger.info("   (Pressione Ctrl+C para parar)")
        logger.info("=" * 60)
        
        # Registrar callback
        self.sync.listen_realtime(self.process_event)
        
        # Loop principal
        try:
            while not shutdown_flag:
                time.sleep(1)
                # A cada 60 segundos, mostrar estatísticas
                if self.processed_count > 0 and self.processed_count % 60 == 0:
                    logger.info(f"📊 Estatísticas: {self.processed_count} processados, {self.error_count} erros")
        except KeyboardInterrupt:
            logger.info("🛑 Interrompido pelo usuário")
        
        logger.info("=" * 60)
        logger.info(f"📊 ESTATÍSTICAS FINAIS")
        logger.info(f"   Eventos processados: {self.processed_count}")
        logger.info(f"   Erros: {self.error_count}")
        logger.info("=" * 60)
        logger.info("👋 Serviço encerrado")


def main():
    """Função principal"""
    
    # Verificar se service account existe
    if not Path(SERVICE_ACCOUNT_PATH).exists():
        logger.error("=" * 60)
        logger.error("❌ ERRO: Service Account Key não encontrado!")
        logger.error("=" * 60)
        logger.error(f"📁 Esperado em: {SERVICE_ACCOUNT_PATH}")
        logger.error("")
        logger.error("📝 Como configurar:")
        logger.error("1. Baixe o serviceAccountKey.json do Firebase Console")
        logger.error("2. Coloque na raiz do projeto")
        logger.error("3. Configure no .env: FIREBASE_SERVICE_ACCOUNT_PATH=serviceAccountKey.json")
        logger.error("=" * 60)
        sys.exit(1)
    
    # Iniciar serviço
    service = RealtimeSync(SERVICE_ACCOUNT_PATH)
    service.start()


if __name__ == "__main__":
    main()

