from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Set it in Vercel environment variables or in backend/.env"
    )

# NullPool: no persistent connections — required for serverless (Vercel)
# Use the Supabase Transaction Pooler URL (port 6543) not the direct connection
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    connect_args={"connect_timeout": 10, "sslmode": "require"},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()