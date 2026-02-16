from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from .config import DATABASE_URL

engine: Engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def init_db() -> None:
    # Minimal table for v1: track processed messages to avoid duplicates
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
