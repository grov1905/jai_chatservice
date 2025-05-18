# infrastructure/config/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = (
    f"postgresql://{os.getenv('PGUSER')}:{os.getenv('PGPASSWORD')}"
    f"@{os.getenv('PGHOST')}:{os.getenv('PGPORT')}/{os.getenv('PGDATABASE')}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    """Crea todas las tablas en la base de datos"""
    try:
        from infrastructure.persistence.models import Base  # Importar tus modelos aquí
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas de la base de datos creadas exitosamente")
    except Exception as e:
        logger.error(f"Error al crear tablas: {str(e)}")
        raise

def get_db():
    """Generador de sesiones para inyección de dependencias"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()