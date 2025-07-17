# file: auth.py

from fastapi import Depends, HTTPException, status
# PERUBAHAN 1: Impor HTTPBearer dan HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt, ExpiredSignatureError
from datetime import datetime, timedelta, timezone

from database import get_db
import models
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# PERUBAHAN 2: Ganti skema keamanan ke HTTPBearer
http_bearer_scheme = HTTPBearer()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# PERUBAHAN 3: Sesuaikan fungsi get_current_user
async def get_current_user(
    # Gunakan skema baru dan tipe data yang sesuai
    token: HTTPAuthorizationCredentials = Depends(http_bearer_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Ambil string token dari objek yang diterima
        token_string = token.credentials
        
        # Dekode token menggunakan string tersebut
        payload = jwt.decode(token_string, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
    except (JWTError, ExpiredSignatureError):
        raise credentials_exception
        
    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception
        
    return user