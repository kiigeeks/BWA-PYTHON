from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Muat variabel dari file .env
load_dotenv()

# Ambil URL dari environment variable
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://root:@localhost/brainwave_db")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ✅ Tambahkan ini:
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
