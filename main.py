# file: main.py

from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlalchemy.orm import Session, joinedload
import uuid
import os
import shutil

# Impor dari file-file lokal Anda
# Ditambahkan verify_password ke dalam impor dari auth
from auth import get_current_user, get_password_hash, create_access_token, get_user, verify_password 
from logic import run_full_analysis
from database import get_db, engine
import models
import schemas
from schemas import StandardResponse, AnalysisResult, User as UserSchema, FilePathPayload, TokenPayload
from tools import convert_edf_to_single_csv, process_edf_with_ica_to_csv
from config import settings

# Membuat semua tabel di database jika belum ada
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Brainwave Analysis API",
    description="API untuk analisis data BWA dan manajemen user.",
    version="1.0.0",
    docs_url="/doc",
    redoc_url=None
)

# Perbaikan pada CORS: Pisahkan string menjadi list
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Status"])
async def read_root():
    return {"message": "BWA API is running and ready!"}

# --- FUNGSI LOGIN YANG SEPENUHNYA DIPERBAIKI ---
@app.post("/v1/bwa/users/login", summary="User Login", response_model=StandardResponse[TokenPayload], tags=["Users"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Session = Depends(get_db)
):
    user = get_user(db, form_data.username)
    # PERBAIKAN: Menggunakan verify_password dari auth, bukan schemas
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # PERBAIKAN: Menggunakan create_access_token dari auth, bukan schemas
    access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
    return StandardResponse(message="Login berhasil", payload=TokenPayload(access_token=access_token, token_type="bearer"))

# ... sisa endpoint lainnya tidak perlu diubah ...
@app.post("/v1/bwa/analyze/", summary="Admin: Register Client and Analyze Data", response_model=StandardResponse[AnalysisResult], tags=["Analysis"])
async def analyze_csv(db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_user), file: UploadFile = File(...), fullname: str = Form(...), username: str = Form(...), password: str = Form(...), company: str = Form(...), gender: str = Form(...), age: int = Form(...), address: str = Form(...), test_date: str = Form(...), test_location: str = Form(...)):
    db_user = get_user(db, username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username for new client already registered")
    hashed_password = get_password_hash(password)
    new_user = models.User(fullname=fullname, username=username, password=hashed_password, company=company, gender=gender, age=age, address=address, test_date=test_date, test_location=test_location)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    user_id = new_user.id
    file_path = f"./{uuid.uuid4()}_{file.filename}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        result = run_full_analysis(file_path, user_id, username)
        return StandardResponse(message="Analisis berhasil dan data client baru telah disimpan.", payload=result)
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

@app.post("/v1/bwa/tools/edf-to-csv", summary="Convert EDF to a single CSV file", response_model=StandardResponse[FilePathPayload], tags=["Tools"])
async def convert_edf_to_csv_endpoint(file: UploadFile = File(...)):
    temp_file_path = f"./{uuid.uuid4()}_{file.filename}"
    with open(temp_file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        output_path = convert_edf_to_single_csv(temp_file_path, file.filename)
        return StandardResponse(message="File EDF berhasil dikonversi menjadi satu file CSV.", payload=FilePathPayload(file_path=output_path))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/v1/bwa/tools/edf-to-ica-csv", summary="Process EDF with ICA and save to a single CSV", response_model=StandardResponse[FilePathPayload], tags=["Tools"])
async def process_edf_with_ica_endpoint(file: UploadFile = File(...)):
    temp_file_path = f"./{uuid.uuid4()}_{file.filename}"
    with open(temp_file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        output_path = process_edf_with_ica_to_csv(temp_file_path, file.filename)
        return StandardResponse(message="File EDF berhasil diproses dengan ICA dan disimpan sebagai CSV.", payload=FilePathPayload(file_path=output_path))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/v1/bwa/users/{user_id}", response_model=StandardResponse[UserSchema], summary="Get User by ID with All Relations", tags=["Users"])
async def read_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_user = db.query(models.User).options(joinedload(models.User.personalities_data), joinedload(models.User.personality_accuracies), joinedload(models.User.cognitive_data), joinedload(models.User.split_brain_data), joinedload(models.User.response_data), joinedload(models.User.fit_jobs), joinedload(models.User.develops), joinedload(models.User.privileges)).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return StandardResponse(message=f"Data user dengan ID {user_id} berhasil ditemukan.", payload=db_user)