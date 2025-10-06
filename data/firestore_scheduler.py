"""
Agendador de Sincronizações Periódicas com Firestore
Executa sincronização em intervalos regulares (cron-like)
"""
import os
import time
import schedule
import logging
from pathlib import Path
from data.firestore_direct import FirestoreSync
import signal
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuração
SERVICE_ACCOUNT_PATH = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'serviceAccountKey.json')
SYNC_INTERVAL_MINUTES = int(os.getenv('FIRESTORE_SYNC_INTERVAL', '5'))  # padrão: 5 minutos

# Controle de shutdown
shutdown_flag = False

def signal_handler(sig, frame):
    """Handler para shutdown gracioso"""
    global shutdown_flag
    logger.info("🛑 Recebido sinal de parada. Encerrando...")
    shutdown_flag = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class FirestoreScheduler:
    """Agendador de sincronizações periódicas"""
    
    def __init__(self, service_account_path: str, interval_minutes: int = 5):
        self.sync = FirestoreSync(service_account_path)
        self.interval_minutes = interval_minutes
        self.total_synced = 0
        self.sync_count = 0
    
    def sync_job(self):
        """Job de sincronização"""
        if not self.sync.is_connected():
            logger.error("❌ Não conectado ao Firestore. Pulando sincronização...")
            return
        
        try:
            logger.info(f"🔄 Iniciando sincronização #{self.sync_count + 1}...")
            count = self.sync.sync_to_jsonl()
            
            self.total_synced += count
            self.sync_count += 1
            
            logger.info(f"✅ Sincronização #{self.sync_count} completa!")
            logger.info(f"   📊 Eventos desta sync: {count}")
            logger.info(f"   📊 Total sincronizado: {self.total_synced}")
            logger.info(f"   ⏰ Próxima sync em {self.interval_minutes} minutos")
            
        except Exception as e:
            logger.error(f"❌ Erro na sincronização: {e}")
    
    def start(self):
        """Inicia o agendador"""
        if not self.sync.is_connected():
            logger.error("❌ Não foi possível conectar ao Firestore!")
            logger.info("Verifique se o serviceAccountKey.json está configurado corretamente")
            sys.exit(1)
        
        logger.info("=" * 60)
        logger.info("📅 AGENDADOR DE SINCRONIZAÇÕES FIRESTORE")
        logger.info("=" * 60)
        logger.info(f"📡 Firestore: Conectado")
        logger.info(f"⏰ Intervalo: A cada {self.interval_minutes} minutos")
        logger.info("=" * 60)
        
        # Executar primeira sincronização imediatamente
        logger.info("🚀 Executando primeira sincronização...")
        self.sync_job()
        
        # Agendar sincronizações periódicas
        schedule.every(self.interval_minutes).minutes.do(self.sync_job)
        
        logger.info("=" * 60)
        logger.info("✅ Agendador iniciado!")
        logger.info("   (Pressione Ctrl+C para parar)")
        logger.info("=" * 60)
        
        # Loop principal
        try:
            while not shutdown_flag:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Interrompido pelo usuário")
        
        logger.info("=" * 60)
        logger.info(f"📊 ESTATÍSTICAS FINAIS")
        logger.info(f"   Sincronizações executadas: {self.sync_count}")
        logger.info(f"   Total de eventos: {self.total_synced}")
        logger.info("=" * 60)
        logger.info("👋 Agendador encerrado")


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
    
    # Iniciar agendador
    scheduler = FirestoreScheduler(SERVICE_ACCOUNT_PATH, SYNC_INTERVAL_MINUTES)
    scheduler.start()


if __name__ == "__main__":
    main()

