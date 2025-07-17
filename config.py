from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Untuk koneksi SQLAlchemy (database.py)
    DATABASE_URL: str

    # Untuk koneksi langsung (logic.py)
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # Untuk otentikasi (auth.py)
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Untuk aplikasi (main.py & logic.py)
    BASE_URL: str
    CORS_ORIGINS: str

    class Config:
        env_file = ".env"

# Membuat satu objek 'settings' yang akan digunakan di seluruh aplikasi
settings = Settings()