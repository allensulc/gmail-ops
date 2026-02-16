from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from .config import DATABASE_URL

def _normalize_db_url(url: str) -> str:
    # Railway often gives postgres:// or postgresql://
    # We want SQLAlchemy psycopg3 driver explicitly.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "postgresql+psycopg://" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

engine: Engine = create_engine(_normalize_db_url(DATABASE_URL), pool_pre_ping=True)

def init_db() -> None:
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS processed_messages (
            message_id TEXT PRIMARY KEY,
            processed_at TIMESTAMPTZ DEFAULT NOW(),
            label_applied TEXT,
            priority INT,
            category TEXT
        );
        """))