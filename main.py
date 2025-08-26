from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from typing import Annotated, Optional, List
from sqlalchemy.orm import Session, joinedload
import uuid
import os
import shutil
import mimetypes
import logging
from fastapi.staticfiles import StaticFiles
from celery import Celery
from fastapi.responses import JSONResponse
from tasks import process_analysis_task
from logger_config import setup_logger
from datetime import date

from tools import process_edf_to_final_csv, convert_edf_to_single_csv, process_edf_with_ica_to_csv
from auth import get_current_user, get_password_hash, create_access_token, get_user, verify_password 
from logic import run_full_analysis
from database import get_db, engine
import models
import schemas
from schemas import StandardResponse, AnalysisResult, User as UserSchema, FilePathPayload, TokenPayload, UserListPayload
from config import settings
from generate_fix import generate_full_report
from generate_fix_pendek import generate_short_report

models.Base.metadata.create_all(bind=engine)

# <-- Perubahan 2: Setup logger untuk otentikasi (sudah ada) -->
# auth_logger = logging.getLogger('auth_logger')
# auth_logger.setLevel(logging.INFO)
# auth_file_handler = logging.FileHandler('auth.log', mode='a')
# auth_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# auth_file_handler.setFormatter(auth_formatter)
# if not auth_logger.handlers:
#     auth_logger.addHandler(auth_file_handler)

# <-- Perubahan 3: Setup logger baru KHUSUS untuk proses analisis -->
# analysis_logger = logging.getLogger('analysis_logger')
# analysis_logger.setLevel(logging.INFO)
# analysis_file_handler = logging.FileHandler('analysis.log', mode='a') # Akan membuat file analysis.log
# analysis_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# analysis_file_handler.setFormatter(analysis_formatter)
# if not analysis_logger.handlers:
#     analysis_logger.addHandler(analysis_file_handler)

analysis_logger = setup_logger('analysis_logger', 'analysis.log')
auth_logger = setup_logger('auth_logger', 'auth.log') # <- Kita juga bisa pakai ini untuk auth_logger!

app = FastAPI(
    title="Brainwave Analysis API",
    description="API untuk analisis data BWA dan manajemen user.",
    version="1.0.0",
    docs_url="/doc",
    redoc_url=None
)

origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", tags=["Status"])
async def read_root():
    return {"message": "BWA API is running and ready!"}

@app.post("/v1/bwa/users/login", summary="User Login", response_model=StandardResponse[TokenPayload], tags=["BWA"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Session = Depends(get_db)
):
    log_data = {'username': form_data.username, 'password': form_data.password}
    auth_logger.info(f"Login attempt with full form_data: {log_data}")
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
    return StandardResponse(message="Login berhasil", payload=TokenPayload(access_token=access_token, token_type="bearer"))

@app.post("/v1/bwa/analyze/", summary="Admin: Register Client and Analyze Data from EDF", status_code=status.HTTP_202_ACCEPTED, tags=["BWA"])
async def analyze_edf(
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_user),
    file: UploadFile = File(...),
    fullname: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    company: str = Form(...),
    gender: str = Form(...),
    age: int = Form(...),
    address: str = Form(...),
    test_date: date = Form(...),
    test_location: str = Form(...),
    pekerjaan: Optional[str] = Form(None),
    operator_name: str = Form(...)
):
    analysis_logger.info(f"===== REQUEST ANALISIS DITERIMA UNTUK USER: {username} =====")

    # --- TUGAS CEPAT 1: Validasi & Buat User (Tetap di sini) ---
    analysis_logger.info("[Langkah 1 & 2] Validasi dan registrasi user.")
    if get_user(db, username):
        raise HTTPException(status_code=400, detail="Username for new client already registered")
    if not file.filename.lower().endswith('.edf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an .edf file.")
    try:
        analysis_logger.info("Mencoba membuat objek user di memori...")
        new_user = models.User(
            fullname=fullname, username=username, password=get_password_hash(password),
            company=company, gender=gender, age=age, address=address,
            test_date=test_date, test_location=test_location, operator=operator_name
        )
        
        analysis_logger.info("Mencoba menambahkan user ke sesi database...")
        db.add(new_user)
        
        analysis_logger.info("Mencoba melakukan commit ke database...")
        db.commit() # <-- Titik rawan error
        
        analysis_logger.info("Mencoba me-refresh instance user...")
        db.refresh(new_user)
        
        analysis_logger.info(f"Registrasi user '{username}' (ID: {new_user.id}) berhasil.")

    except Exception as e:
        # JIKA TERJADI ERROR, LOG INI AKAN TERCATAT SEBELUM CRASH!
        analysis_logger.error(f"GAGAL TOTAL SAAT REGISTRASI USER! Error: {e}", exc_info=True)
        db.rollback() # Batalkan transaksi yang gagal
        raise HTTPException(status_code=500, detail=f"Database error during user registration: {e}")

    # --- TUGAS CEPAT 2: Simpan & Konversi File EDF (Tetap di sini) ---
    unique_id = uuid.uuid4()
    temp_edf_path = f"./{unique_id}_{file.filename}"
    processed_csv_path = f"./{unique_id}_processed.csv"
    try:
        analysis_logger.info(f"[Langkah 3] Menyimpan & konversi file EDF ke CSV.")
        with open(temp_edf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        process_edf_to_final_csv(temp_edf_path, processed_csv_path) # Dari tools.py
        analysis_logger.info(f"File CSV berhasil dibuat di '{processed_csv_path}'.")

        # --- TUGAS BERAT: Delegasikan ke Celery! ---
        analysis_logger.info(f"Mendelegasikan analisis penuh untuk user ID {new_user.id} ke background worker...")
        process_analysis_task.delay(
            processed_csv_path, new_user.id, username, pekerjaan
        )

        # --- LANGSUNG KEMBALIKAN RESPONSE (Jangan Menunggu) ---
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "message": "Permintaan analisis diterima dan sedang diproses di latar belakang.",
                "user_id": new_user.id
            }
        )
    except Exception as e:
        analysis_logger.error(f"Gagal pada tahap persiapan awal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gagal pada tahap persiapan awal: {e}")
    finally:
        # Hanya membersihkan file .edf, karena .csv dibutuhkan oleh Celery
        if os.path.exists(temp_edf_path):
            os.remove(temp_edf_path)

@app.post("/v1/bwa/tools/edf-to-csv", summary="Convert EDF to a single CSV file", response_model=StandardResponse[FilePathPayload], tags=["BWA"])
async def convert_edf_to_csv_endpoint(file: UploadFile = File(...)):
    temp_file_path = f"./{uuid.uuid4()}_{file.filename}"
    with open(temp_file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        output_path = convert_edf_to_single_csv(temp_file_path, file.filename)
        clean_path = output_path.replace('\\', '/')
        return StandardResponse(message="File EDF berhasil dikonversi.", payload=FilePathPayload(file_path=clean_path))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/v1/bwa/tools/edf-to-ica-csv", summary="Process EDF with ICA and save to a single CSV", response_model=StandardResponse[FilePathPayload], tags=["BWA"])
async def process_edf_with_ica_endpoint(file: UploadFile = File(...)):
    temp_file_path = f"./{uuid.uuid4()}_{file.filename}"
    with open(temp_file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        output_path = process_edf_with_ica_to_csv(temp_file_path, file.filename)
        clean_path = output_path.replace('\\', '/')
        return StandardResponse(message="File EDF berhasil diproses dengan ICA.", payload=FilePathPayload(file_path=clean_path))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get(
    "/v1/bwa/tools/download", 
    summary="Download a generated file", 
    tags=["BWA"],
    responses={
        200: {"description": "Returns the requested file for download."},
        404: {"description": "File not found"},
    }
)
async def download_file(filepath: str):
    full_path = filepath

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File tidak ditemukan")

    mime_type, _ = mimetypes.guess_type(filepath)
    return FileResponse(
        path=filepath,
        media_type=mime_type or "application/octet-stream",
        filename=os.path.basename(filepath)
    )

@app.delete("/v1/bwa/users/{user_id}", response_model=StandardResponse, summary="Admin: Delete a User", tags=["BWA"])
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_user)
):
    """
    Menghapus user dan semua data terkaitnya. Tindakan ini tidak bisa dibatalkan.
    Hanya bisa diakses oleh user dengan role 'admin'.
    """
    # 1. Otorisasi: Cek apakah user yang login adalah admin
    if current_admin.roles != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki izin untuk menghapus user."
        )

    # 2. Cari user yang akan dihapus
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()

    # 3. Handle jika user tidak ditemukan
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User dengan ID {user_id} tidak ditemukan."
        )
        
    # 4. Mencegah admin menghapus akunnya sendiri
    if user_to_delete.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin tidak dapat menghapus akunnya sendiri."
        )

    db.delete(user_to_delete)
    db.commit()

    return StandardResponse(message=f"User '{user_to_delete.username}' (ID: {user_id}) dan semua data terkaitnya berhasil dihapus.")

@app.get("/v1/bwa/users/{user_id}", response_model=StandardResponse[UserSchema], summary="Get User by ID with All Relations", tags=["BWA"])
async def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).options(
        joinedload(models.User.personalities_data), 
        # joinedload(models.User.personality_accuracies), 
        joinedload(models.User.cognitive_data), 
        # joinedload(models.User.split_brain_data), 
        joinedload(models.User.response_data),
        joinedload(models.User.roc_curves)
    ).filter(models.User.id == user_id).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return StandardResponse(message=f"Data user dengan ID {user_id} berhasil ditemukan.", payload=db_user)

@app.get("/v1/bwa/users/",response_model=StandardResponse[UserListPayload],summary="Get All Users with Infinite Scroll (Descending)",tags=["BWA"])
async def read_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    limit: int = 10,
    last_id: Optional[int] = -1,
    search: Optional[str] = None
):
    """
    Mengambil daftar pengguna dengan paginasi berbasis kursor (infinite scroll)
    secara descending (data terbaru dulu). Endpoint ini hanya akan
    mengembalikan pengguna dengan peran 'user'.
    """
    query = db.query(models.User)
    
    query = query.filter(models.User.roles == 'user')
    
    if search:
        query = query.filter(models.User.fullname.ilike(f"%{search}%"))
        
    if last_id != -1:
        query = query.filter(models.User.id < last_id)
        
    query_limit = limit + 1
    users = query.order_by(models.User.id.desc()).limit(query_limit).all()
    
    has_more = len(users) > limit
    users_to_return = users[:limit]
    
    last_id_in_response = None
    if users_to_return:
        last_id_in_response = users_to_return[-1].id
        
    payload_data = UserListPayload(
        data=users_to_return,
        last_id=last_id_in_response,
        has_more=has_more
    )
    
    return StandardResponse(
        message=f"Berhasil mengambil data {len(users_to_return)} user.",
        payload=payload_data
    )