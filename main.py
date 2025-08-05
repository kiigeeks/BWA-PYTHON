from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from typing import Annotated, Optional
from sqlalchemy.orm import Session, joinedload
import uuid
import os
import shutil
import mimetypes

from tools import process_edf_to_final_csv, convert_edf_to_single_csv, process_edf_with_ica_to_csv
from auth import get_current_user, get_password_hash, create_access_token, get_user, verify_password 
from logic import run_full_analysis
from database import get_db, engine
import models
import schemas
from schemas import StandardResponse, AnalysisResult, User as UserSchema, FilePathPayload, TokenPayload
from tools import convert_edf_to_single_csv, process_edf_with_ica_to_csv
from config import settings
from generate_fix import generate_full_report

models.Base.metadata.create_all(bind=engine)

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
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
    return StandardResponse(message="Login berhasil", payload=TokenPayload(access_token=access_token, token_type="bearer"))

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
    test_date: str = Form(...), 
    test_location: str = Form(...),
    pekerjaan: Optional[str] = Form(None),
    operator_name: str = Form(...)
):
    # --- VALIDASI INPUT ---
    db_user = get_user(db, username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username for new client already registered")
    if not file.filename.lower().endswith('.edf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an .edf file.")

    # --- REGISTRASI USER ---
    hashed_password = get_password_hash(password)
    new_user = models.User(
        fullname=fullname, username=username, password=hashed_password, 
        company=company, gender=gender, age=age, address=address, 
        test_date=test_date, test_location=test_location
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # --- PERSIAPAN FILE PATHS ---
    unique_id = uuid.uuid4()
    temp_edf_path = f"./{unique_id}_{file.filename}"
    processed_csv_path = f"./{unique_id}_processed.csv"
    
    with open(temp_edf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    try:
        # --- PROSES & ANALISIS UTAMA ---
        print("Starting EDF to CSV processing...")
        process_edf_to_final_csv(temp_edf_path, processed_csv_path)
        
        print("Starting full analysis on processed CSV...")
        result = run_full_analysis(processed_csv_path, new_user.id, username)
        
        # --- PEMBUATAN LAPORAN ---
        print("\n--- Memulai integrasi pembuatan Laporan Panjang (PDF) ---")
        try:
            ALLOWED_PERSONALITIES = {"Openess", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"}
            ALLOWED_COGNITIVE_KEYS = {"Kraepelin Test (Numerik)", "WCST (Logika)", "Digit Span (Short Term Memory)"}
            
            cognitive_key_map = {
                "KRAEPELIN TEST": "Kraepelin Test (Numerik)",
                "WCST": "WCST (Logika)",
                "DIGIT SPAN": "Digit Span (Short Term Memory)"
            }

            big_five_results = result['big_five']
            cognitive_results = result['cognitive_function']
            
            valid_personality_results = [
                p for p in big_five_results if p.get('PERSONALITY', '').title() in ALLOWED_PERSONALITIES
            ]
            valid_cognitive_results = [
                c for c in cognitive_results if cognitive_key_map.get(c.get('TEST', '').upper()) in ALLOWED_COGNITIVE_KEYS
            ]

            if not valid_personality_results or not valid_cognitive_results:
                 print("   -> Peringatan: Hasil analisis Big Five atau Kognitif kosong. Laporan tidak dibuat.")
            else:
                top_personality_data = max(big_five_results, key=lambda x: x.get('SCORE', 0))
                top_cognitive_data = max(cognitive_results, key=lambda x: x.get('SCORE', 0))
                tipe_kepribadian_tertinggi = top_personality_data['PERSONALITY'].title()
                kognitif_nama_tertinggi = top_cognitive_data['TEST']
                kognitif_utama_key = cognitive_key_map.get(kognitif_nama_tertinggi.upper())

                output_dir_topoplot = "static/topoplots"
                topoplot_behavior_filename = f"{new_user.username}_topoplot_{top_personality_data['PERSONALITY'].lower().replace(' ', '_')}.png"
                topoplot_cognitive_filename = f"{new_user.username}_topoplot_{kognitif_nama_tertinggi.lower().replace(' ', '_')}.png"
                topoplot_path_behavior = os.path.join(output_dir_topoplot, topoplot_behavior_filename)
                topoplot_path_cognitive = os.path.join(output_dir_topoplot, topoplot_cognitive_filename)

                biodata_kandidat = {
                    "Nama": new_user.fullname,
                    "Jenis kelamin": new_user.gender,
                    "Usia": f"{new_user.age} Tahun",
                    "Alamat": new_user.address,
                    "Keperluan Test": "Profiling dengan Brain Wave Analysis response",
                    "Tanggal Test": new_user.test_date.strftime('%d %B %Y') if new_user.test_date else "-",
                    "Tempat Test": new_user.test_location,
                    "Operator": operator_name 
                }
                
                output_dir = "static/long_report"
                os.makedirs(output_dir, exist_ok=True)
                nama_file_output = f"{output_dir}/{new_user.username}_long_report.pdf"
                
                print(f"   -> Memanggil generate_full_report untuk membuat file: {nama_file_output}")
                generate_full_report(
                    tipe_kepribadian=tipe_kepribadian_tertinggi,
                    kognitif_utama_key=kognitif_utama_key,
                    pekerjaan=pekerjaan,
                    model_ai="llama3.1:8b",
                    nama_file_output=nama_file_output,
                    biodata_kandidat=biodata_kandidat,
                    topoplot_path_behaviour=topoplot_path_behavior,
                    topoplot_path_cognitive=topoplot_path_cognitive
                )
                
                print(f"   -> Menyimpan path laporan ke database...")
                user_to_update = db.query(models.User).filter(models.User.id == new_user.id).first()
                if user_to_update:
                    user_to_update.laporan_panjang = nama_file_output
                    db.commit()
                    print("   -> Path berhasil disimpan.")
                else:
                    print("   -> Peringatan: Gagal menemukan user untuk update path laporan.")
                result['long_report_url'] = f"{settings.BASE_URL}/{nama_file_output}"
                print(f"   -> URL Laporan ditambahkan ke payload: {result['long_report_url']}")
        except Exception as report_error:
            print(f"   -> !!! Terjadi error saat membuat laporan PDF: {report_error}")
        return StandardResponse(message="Analisis dari file EDF berhasil dan data client baru telah disimpan.", payload=result)
        
    except Exception as e:
        db.delete(new_user)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
        
    finally:
        # --- CLEANUP ---
        if os.path.exists(temp_edf_path):
            os.remove(temp_edf_path)
        if os.path.exists(processed_csv_path):
            os.remove(processed_csv_path)
        for temp_file in ["cleaning.csv", "cleaning2.csv"]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

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
async def read_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_user = db.query(models.User).options(
        joinedload(models.User.personalities_data), 
        joinedload(models.User.personality_accuracies), 
        joinedload(models.User.cognitive_data), 
        joinedload(models.User.split_brain_data), 
        joinedload(models.User.response_data),
        joinedload(models.User.roc_curves)
    ).filter(models.User.id == user_id).first()
    
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return StandardResponse(message=f"Data user dengan ID {user_id} berhasil ditemukan.", payload=db_user)