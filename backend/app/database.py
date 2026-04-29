from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import get_settings

# Database configuration with SSL support
settings = get_settings()

connect_args = {}
if not settings.database_url.startswith("sqlite"):
    # Add a connection timeout to prevent hangs
    connect_args["connect_timeout"] = 5
    
    if settings.database_ssl:
        ssl_config = {}
        if settings.database_ssl_ca:
            ssl_config["ca"] = settings.database_ssl_ca
        
        if ssl_config:
            connect_args["ssl"] = ssl_config

engine = create_engine(
    settings.database_url, 
    connect_args=connect_args, 
    future=True,
    pool_pre_ping=True # Keep this for stability if the hang is fixed
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
