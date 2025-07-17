# file: main.py

from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from typing import Annotated
import uuid
import os
import shutil
from auth import get_current_user

# Import dari file lokal
from logic import run_full_analysis
from database import get_db
import models
import schemas # <-- Impor semua schemas
from auth import create_access_token, get_password_hash, verify_password, get_user

# <-- 1. Impor skema respons yang baru
from schemas import StandardResponse, TokenPayload, AnalysisResult, User as UserSchema

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================
# ENDPOINT LOGIN
# ==================================

@app.post(
    "/v1/bwa/users/login",
    summary="User Login",
    response_model=StandardResponse[TokenPayload]
)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """
    Login user dengan username dan password, mengembalikan token JWT.
    """
    user = get_user(db, form_data.username)
    
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    # <-- 3. Ubah format return sesuai skema baru
    return StandardResponse(
        message="Login berhasil",
        payload=TokenPayload(access_token=access_token, token_type="bearer")
    )

# ==================================
# ENDPOINT ANALISIS (REGISTRASI USER)
# ==================================

@app.post(
    "/v1/bwa/analyze/",
    summary="Register User and Analyze Data",
    response_model=StandardResponse[AnalysisResult]
)
async def analyze_csv(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    fullname: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    company: str = Form(...),
    gender: str = Form(...),
    age: int = Form(...),
    address: str = Form(...),
    test_date: str = Form(...),
    test_location: str = Form(...)
):
    """
    Mendaftarkan user baru, menyimpan password yang sudah di-hash, dan menjalankan analisis.
    """
    db_user = get_user(db, username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(password)

    new_user = models.User(
        fullname=fullname,
        username=username,
        password=hashed_password,
        company=company,
        gender=gender,
        age=age,
        address=address,
        test_date=test_date,
        test_location=test_location
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    user_id = new_user.id

    file_path = f"./{uuid.uuid4()}_{file.filename}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = run_full_analysis(file_path, user_id, username)
        # <-- 5. Ubah format return sesuai skema baru
        return StandardResponse(
            message="Analisis berhasil dan data user telah disimpan.",
            payload=result
        )

    except Exception as e:
        db.delete(new_user)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        for temp_file in ["cleaning.csv", "cleaning2.csv"]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

# ==================================
# ENDPOINT UNTUK GET USER BY ID (DENGAN RELASI)
# ==================================

@app.get(
    "/v1/bwa/users/{user_id}",
    # <-- 6. Ubah response_model ke format standar baru
    response_model=StandardResponse[UserSchema],
    summary="Get User by ID with All Relations"
)
async def read_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Mengambil data seorang pengguna berdasarkan ID beserta semua data relasinya.
    """

    db_user = db.query(models.User).options(
        joinedload(models.User.personalities_data),
        joinedload(models.User.personality_accuracies),
        joinedload(models.User.cognitive_data),
        joinedload(models.User.split_brain_data),
        joinedload(models.User.response_data),
        joinedload(models.User.fit_jobs),
        joinedload(models.User.develops),
        joinedload(models.User.privileges)
    ).filter(models.User.id == user_id).first()
    
    if db_user is None:
        # Untuk error, FastAPI akan otomatis mengirim format standar { "detail": "User not found" }
        raise HTTPException(status_code=404, detail="User not found")
        
    # <-- 7. Ubah format return sesuai skema baru
    return StandardResponse(
        message=f"Data user dengan ID {user_id} berhasil ditemukan.",
        payload=db_user
    )