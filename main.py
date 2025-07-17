from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from typing import Annotated
import uuid
import os
import shutil

# Import pustaka untuk pemrosesan EDF
import mne
import pandas as pd

# Import dari file lokal
from auth import get_current_user
from logic import run_full_analysis
from database import get_db
import models
import schemas
from auth import create_access_token, get_password_hash, verify_password, get_user

# Impor skema respons
from schemas import StandardResponse, TokenPayload, AnalysisResult, User as UserSchema

# <-- Tambahkan impor skema baru
from schemas import FilePathPayload

# ==================================
# KONFIGURASI APLIKASI
# ==================================

# file: main.py

app = FastAPI(
    title="Brainwave Analysis API",
    description="API untuk analisis data BWA dan manajemen user.",
    version="1.0.0",
    docs_url="/doc"
)

# Direktori untuk menyimpan file output
OUTPUT_DIR = "output_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================
# ENDPOINT ROOT / HEALTH CHECK
# ==================================
@app.get("/v1/bwa/", tags=["Status"])
async def read_root():
    """
    Endpoint untuk memeriksa apakah API sedang berjalan.
    """
    return {"message": "BWA API sudah jalan"}

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


# =========================================================
# ENDPOINT 1: Konversi EDF ke CSV (Semua Channel 1 File)
# =========================================================
@app.post(
    "/v1/bwa/tools/edf-to-csv",
    summary="Convert EDF to a single CSV file",
    response_model=StandardResponse[FilePathPayload]
)
async def convert_edf_to_csv(file: UploadFile = File(...)):
    """
    Mengonversi file .edf menjadi satu file .csv yang berisi semua channel.
    
    - **Input**: file .edf
    - **Output**: message dan payload berisi path ke file .csv yang disimpan.
    """
    
    # Membuat path sementara untuk menyimpan file upload
    temp_file_path = f"./{uuid.uuid4()}_{file.filename}"
    with open(temp_file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # Membaca file EDF menggunakan MNE
        raw = mne.io.read_raw_edf(temp_file_path, preload=True)
        
        # Mengonversi data ke pandas DataFrame
        df = raw.to_data_frame()
        
        # Membuat nama file output yang unik di dalam direktori output
        base_filename = os.path.splitext(file.filename)[0]
        output_filename = f"{base_filename}_converted.csv"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # Menyimpan DataFrame ke CSV
        df.to_csv(output_path, index=False)
        
        return StandardResponse(
            message="File EDF berhasil dikonversi menjadi satu file CSV.",
            payload=FilePathPayload(file_path=output_path)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses file EDF: {str(e)}")
    
    finally:
        # Membersihkan file sementara yang diupload
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# ======================================================================
# ENDPOINT 2: Proses ICA pada EDF dan simpan ke CSV
# ======================================================================
@app.post(
    "/v1/bwa/tools/edf-to-ica-csv",
    summary="Process EDF with ICA and save to a single CSV",
    response_model=StandardResponse[FilePathPayload]
)
async def process_edf_with_ica(file: UploadFile = File(...)):
    """
    Memproses file .edf dengan filter dan ICA, kemudian menyimpannya ke satu file .csv.
    
    - **Input**: file .edf
    - **Output**: message dan payload berisi path ke file .csv yang telah diproses.
    """
    
    # Membuat path sementara untuk menyimpan file upload
    temp_file_path = f"./{uuid.uuid4()}_{file.filename}"
    with open(temp_file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # 1. Load full EDF
        raw_full = mne.io.read_raw_edf(temp_file_path, preload=True)
        
        # 2. Pilih channel EEG saja untuk ICA
        eeg_raw = raw_full.copy().pick_types(eeg=True)
        
        # Periksa apakah ada channel EEG
        if not eeg_raw.ch_names:
            raise HTTPException(status_code=400, detail="Tidak ditemukan channel EEG di dalam file EDF.")

        # 3. Filter dulu (ICA butuh bandpass clean signal)
        eeg_raw.filter(1., 40., fir_design='firwin')

        # 4. Terapkan ICA
        # n_components disarankan lebih kecil dari jumlah channel EEG
        n_components = min(15, len(eeg_raw.ch_names) - 1)
        if n_components < 1:
            raise HTTPException(status_code=400, detail="Jumlah channel EEG tidak cukup untuk menjalankan ICA.")
            
        ica = mne.preprocessing.ICA(n_components=n_components, random_state=42)
        ica.fit(eeg_raw)
        
        # Di sini bisa ditambahkan logika untuk exlude komponen secara otomatis
        # Untuk saat ini kita langsung apply
        
        # 5. Terapkan ICA ke data EEG
        ica.apply(eeg_raw)

        # 6. Masukkan kembali data EEG hasil ICA ke data lengkap
        for ch_name in eeg_raw.ch_names:
            if ch_name in raw_full.ch_names:
                idx_full = raw_full.ch_names.index(ch_name)
                idx_eeg = eeg_raw.ch_names.index(ch_name)
                raw_full._data[idx_full] = eeg_raw._data[idx_eeg]

        # 7. Ekspor semua channel ke CSV
        df_cleaned = raw_full.to_data_frame()
        
        base_filename = os.path.splitext(file.filename)[0]
        output_filename = f"{base_filename}_ica_cleaned.csv"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        df_cleaned.to_csv(output_path, index=False)

        return StandardResponse(
            message="File EDF berhasil diproses dengan ICA dan disimpan sebagai CSV.",
            payload=FilePathPayload(file_path=output_path)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses file dengan ICA: {str(e)}")

    finally:
        # Membersihkan file sementara yang diupload
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# ==================================
# ENDPOINT UNTUK GET USER BY ID (DENGAN RELASI)
# ==================================
@app.get(
    "/v1/bwa/users/{user_id}",
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
        raise HTTPException(status_code=404, detail="User not found")
        
    return StandardResponse(
        message=f"Data user dengan ID {user_id} berhasil ditemukan.",
        payload=db_user
    )