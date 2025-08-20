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
import logging # <-- Perubahan 1: Impor modul logging
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
auth_logger = logging.getLogger('auth_logger')
auth_logger.setLevel(logging.INFO)
auth_file_handler = logging.FileHandler('auth.log', mode='a')
auth_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
auth_file_handler.setFormatter(auth_formatter)
if not auth_logger.handlers:
    auth_logger.addHandler(auth_file_handler)

# <-- Perubahan 3: Setup logger baru KHUSUS untuk proses analisis -->
analysis_logger = logging.getLogger('analysis_logger')
analysis_logger.setLevel(logging.INFO)
analysis_file_handler = logging.FileHandler('analysis.log', mode='a') # Akan membuat file analysis.log
analysis_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
analysis_file_handler.setFormatter(analysis_formatter)
if not analysis_logger.handlers:
    analysis_logger.addHandler(analysis_file_handler)


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

# <-- Perubahan 4: Endpoint analyze_edf dirombak total dengan logging dan error handling bertingkat -->
@app.post("/v1/bwa/analyze/", summary="Admin: Register Client and Analyze Data from EDF", response_model=StandardResponse[AnalysisResult], tags=["BWA"])
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
    analysis_logger.info(f"===== PROSES ANALISIS BARU DIMULAI UNTUK USER: {username} =====")
    
    # --- LANGKAH 1: VALIDASI INPUT ---
    analysis_logger.info("[Langkah 1] Memulai validasi input.")
    try:
        db_user = get_user(db, username)
        if db_user:
            raise HTTPException(status_code=400, detail="Username for new client already registered")
        if not file.filename.lower().endswith('.edf'):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an .edf file.")
        analysis_logger.info("[Langkah 1] Validasi input berhasil.")
    except Exception as e:
        analysis_logger.error(f"[Langkah 1] Gagal validasi input: {e}", exc_info=True)
        raise e # Lemparkan kembali exception asli

    # --- LANGKAH 2: REGISTRASI USER ---
    new_user = None # Inisialisasi new_user
    try:
        analysis_logger.info("[Langkah 2] Memulai registrasi user baru.")
        hashed_password = get_password_hash(password)
        new_user = models.User(
            fullname=fullname, username=username, password=hashed_password, 
            company=company, gender=gender, age=age, address=address, 
            test_date=test_date, test_location=test_location
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        analysis_logger.info(f"[Langkah 2] Registrasi user '{username}' (ID: {new_user.id}) berhasil.")
    except Exception as e:
        analysis_logger.error(f"[Langkah 2] Gagal registrasi user: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan data user baru ke database: {e}")

    # --- PERSIAPAN FILE & PROSES UTAMA ---
    unique_id = uuid.uuid4()
    temp_edf_path = f"./{unique_id}_{file.filename}"
    processed_csv_path = f"./{unique_id}_processed.csv"
    
    try:
        # --- LANGKAH 3: SIMPAN & PROSES FILE EDF KE CSV ---
        try:
            analysis_logger.info(f"[Langkah 3] Menyimpan file upload ke '{temp_edf_path}'.")
            with open(temp_edf_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            analysis_logger.info("[Langkah 3] Memulai konversi EDF ke CSV dengan ICA, POW, dan PM.")
            process_edf_to_final_csv(temp_edf_path, processed_csv_path)
            analysis_logger.info(f"[Langkah 3] File CSV berhasil dibuat di '{processed_csv_path}'.")
        except Exception as e:
            analysis_logger.error(f"[Langkah 3] Gagal pada tahap pemrosesan file: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Gagal saat pemrosesan file EDF ke CSV: {e}")

        # --- LANGKAH 4: JALANKAN ANALISIS LOGIKA UTAMA ---
        try:
            analysis_logger.info("[Langkah 4] Memulai analisis logika utama (Big Five, Cognitive, dll).")
            result = run_full_analysis(processed_csv_path, new_user.id, username)
            analysis_logger.info("[Langkah 4] Analisis logika utama berhasil diselesaikan.")
        except Exception as e:
            analysis_logger.error(f"[Langkah 4] Gagal pada tahap analisis logika: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Gagal saat menjalankan analisis inti: {e}")

        # --- LANGKAH 5: PEMBUATAN LAPORAN PANJANG (PDF) ---
        try:
            analysis_logger.info("[Langkah 5] Memulai pembuatan Laporan Panjang (PDF).")
            ALLOWED_PERSONALITIES = {"Openess", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"}
            ALLOWED_COGNITIVE_KEYS = {"Kraepelin Test (Numerik)", "WCST (Logika)", "Digit Span (Short Term Memory)"}
            cognitive_key_map = {
                "KRAEPELIN TEST": "Kraepelin Test (Numerik)",
                "WCST": "WCST (Logika)",
                "DIGIT SPAN": "Digit Span (Short Term Memory)"
            }
            cognitive_db_name_map = {"KRAEPELIN TEST": "Kraepelin", "WCST": "WCST", "DIGIT SPAN": "Digit Span"}

            top_personality_data = max(result['big_five'], key=lambda x: x.get('SCORE', 0))
            top_cognitive_data = max(result['cognitive_function'], key=lambda x: x.get('SCORE', 0))
            tipe_kepribadian_tertinggi = top_personality_data['PERSONALITY'].title()
            kognitif_nama_tertinggi = top_cognitive_data['TEST']
            kognitif_utama_key = cognitive_key_map.get(kognitif_nama_tertinggi.upper())

            if not tipe_kepribadian_tertinggi in ALLOWED_PERSONALITIES or not kognitif_utama_key in ALLOWED_COGNITIVE_KEYS:
                 raise ValueError("Hasil analisis Big Five atau Kognitif tidak valid/kosong.")

            output_dir_topoplot = "static/topoplots"
            topoplot_path_behavior = os.path.join(output_dir_topoplot, f"{new_user.username}_topoplot_{top_personality_data['PERSONALITY'].lower().replace(' ', '_')}.png")
            topoplot_path_cognitive = os.path.join(output_dir_topoplot, f"{new_user.username}_topoplot_{kognitif_nama_tertinggi.lower().replace(' ', '_')}.png")

            biodata_kandidat = {
                "Nama": new_user.fullname, "Jenis kelamin": new_user.gender, "Usia": f"{new_user.age} Tahun",
                "Alamat": new_user.address, "Keperluan Test": "Profiling dengan Brain Wave Analysis response",
                "Tanggal Test": new_user.test_date.strftime('%d %B %Y') if new_user.test_date else "-",
                "Tempat Test": new_user.test_location, "Operator": operator_name 
            }
            
            output_dir = "static/long_report"
            os.makedirs(output_dir, exist_ok=True)
            nama_file_output_panjang = f"{output_dir}/{new_user.username}_long_report.pdf"
            
            analysis_logger.info(f"   -> Memanggil generate_full_report untuk {nama_file_output_panjang}")
            person_job_fit_text = generate_full_report(
                tipe_kepribadian=tipe_kepribadian_tertinggi, kognitif_utama_key=kognitif_utama_key, pekerjaan=pekerjaan,
                model_ai="deepseek-r1:1.5b", nama_file_output=nama_file_output_panjang, biodata_kandidat=biodata_kandidat,
                topoplot_path_behaviour=topoplot_path_behavior, topoplot_path_cognitive=topoplot_path_cognitive
            )
            
            user_to_update = db.query(models.User).filter(models.User.id == new_user.id).first()
            user_to_update.laporan_panjang = nama_file_output_panjang
            db.commit()
            result['long_report_url'] = f"{settings.BASE_URL}/{nama_file_output_panjang}"
            analysis_logger.info("[Langkah 5] Pembuatan laporan panjang berhasil.")
        except Exception as e:
            analysis_logger.error(f"[Langkah 5] Gagal saat membuat laporan PDF panjang: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Gagal saat generate laporan panjang: {e}")

        # --- LANGKAH 6: PEMBUATAN LAPORAN PENDEK (PDF) ---
        try:
            analysis_logger.info("[Langkah 6] Memulai pembuatan Laporan Pendek (PDF).")
            personality_details = db.query(models.Personality).filter(models.Personality.name == tipe_kepribadian_tertinggi).first()
            cognitive_db_name = cognitive_db_name_map.get(kognitif_nama_tertinggi.upper())
            cognitive_details = db.query(models.Test).filter(models.Test.name == cognitive_db_name).first()

            if not personality_details or not cognitive_details:
                raise ValueError("Gagal mendapatkan detail kepribadian/kognitif dari DB untuk laporan pendek.")

            output_dir_pendek = "static/short_report"
            os.makedirs(output_dir_pendek, exist_ok=True)
            nama_file_output_pendek = f"{output_dir_pendek}/{new_user.username}_short_report.pdf"

            analysis_logger.info(f"   -> Memanggil generate_short_report untuk {nama_file_output_pendek}")
            generate_short_report(
                tipe_kepribadian=tipe_kepribadian_tertinggi, kognitif_utama_key=kognitif_utama_key, pekerjaan=pekerjaan,
                model_ai="deepseek-r1:1.5b", nama_file_output=nama_file_output_pendek, biodata_kandidat=biodata_kandidat,
                topoplot_path_behaviour=topoplot_path_behavior, topoplot_path_cognitive=topoplot_path_cognitive,
                personality_title=personality_details.title, personality_desc=personality_details.description,
                cognitive_title=cognitive_details.title, cognitive_desc=cognitive_details.description,
                person_job_fit_text_from_long_report=person_job_fit_text
            )
            
            user_to_update.laporan_pendek = nama_file_output_pendek
            db.commit()
            result['short_report_url'] = f"{settings.BASE_URL}/{nama_file_output_pendek}"
            analysis_logger.info("[Langkah 6] Pembuatan laporan pendek berhasil.")
        except Exception as e:
            analysis_logger.error(f"[Langkah 6] Gagal saat membuat laporan PDF pendek: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Gagal saat generate laporan pendek: {e}")

        analysis_logger.info(f"===== PROSES ANALISIS SELESAI DENGAN SUKSES UNTUK USER: {username} =====")
        return StandardResponse(message="Analisis dari file EDF berhasil dan data client baru telah disimpan.", payload=result)

    finally:
        # --- BLOK PEMBERSIHAN FILE SEMENTARA ---
        analysis_logger.info("Memulai pembersihan file sementara.")
        if os.path.exists(temp_edf_path):
            os.remove(temp_edf_path)
            analysis_logger.info(f"   -> File '{temp_edf_path}' dihapus.")
        if os.path.exists(processed_csv_path):
            os.remove(processed_csv_path)
            analysis_logger.info(f"   -> File '{processed_csv_path}' dihapus.")
        for temp_file in ["cleaning.csv", "cleaning2.csv"]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                analysis_logger.info(f"   -> File '{temp_file}' dihapus.")

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
    last_id: Optional[int] = None,
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
        
    if last_id is not None:
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