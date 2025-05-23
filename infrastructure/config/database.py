# infrastructure/config/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, before_log

load_dotenv()

logger = logging.getLogger(__name__)

# Configuración optimizada para Neon.tech
DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('PGUSER')}:{os.getenv('PGPASSWORD')}"
    f"@{os.getenv('PGHOST')}:{os.getenv('PGPORT')}/{os.getenv('PGDATABASE')}"
    f"?sslmode={os.getenv('SSLMODE')}"  # Neon recomienda SSL pero no requiere certificados locales
    "&connect_timeout=10"  # Timeout de conexión de 10 segundos
)

# Configuración mejorada del engine para Neon
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # Verifica conexiones antes de usarlas
    isolation_level="READ COMMITTED",  # Nivel de aislamiento más seguro
    pool_recycle=300,            # Recicla conexiones cada 5 minutos (Neon tiene timeout de 5 min)
    pool_size=5,                 # Conexiones mantenidas en el pool
    max_overflow=10,             # Conexiones adicionales permitidas
    pool_timeout=30,             # Espera 30 segundos para obtener conexión
    echo_pool=os.getenv('DB_ECHO_POOL', '').lower() == 'true',  # Logs del pool
    echo=os.getenv('DB_ECHO', '').lower() == 'true'             # Logs de queries SQL
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Mejor para aplicaciones web/largo tiempo de vida
)

Base = declarative_base()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    before=before_log(logger, logging.INFO)
)
def init_db():
    """Crea todas las tablas en la base de datos con reintentos automáticos"""
    try:
        from infrastructure.persistence.models import Base  # Importar tus modelos aquí
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas de la base de datos creadas exitosamente")
    except Exception as e:
        logger.error(f"Error al crear tablas: {str(e)}")
        raise

def get_db():
    """
    Generador de sesiones para inyección de dependencias con manejo robusto
    Uso típico en FastAPI:
    def endpoint(db: Session = Depends(get_db)):
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Commit explícito si todo va bien
    except Exception as e:
        db.rollback()
        logger.error(f"Error en la sesión de DB: {str(e)}")
        raise
    finally:
        db.close()