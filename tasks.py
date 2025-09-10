# filename: tasks.py

from celery import Celery
import os
import shutil
import traceback # <-- 1. IMPORT TRACEBACK

# Impor fungsi-fungsi utama dari file lain
from logic import run_full_analysis
from generate_fix import generate_full_report
from generate_fix_pendek import generate_short_report
from database import SessionLocal
import models
from config import settings
from logger_config import setup_logger

celery_app = Celery('tasks', broker='redis://localhost:6379/0')
analysis_logger = setup_logger('analysis_logger', 'analysis.log')

@celery_app.task
def process_analysis_task(
    processed_csv_path, user_id, username, pekerjaan
):
    analysis_logger.info(f"CELERY WORKER: Memulai analisis untuk user ID {user_id}...")
    db = SessionLocal()
    user = None # Inisialisasi user di luar try
    try:
        # 2. Ambil objek user di awal untuk pencatatan error jika gagal
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            # Jika user tidak ditemukan, catat dan hentikan.
            analysis_logger.error(f"CELERY WORKER ERROR: User dengan ID {user_id} tidak ditemukan di database. Proses dihentikan.")
            return

        # --- LANGKAH A: JALANKAN ANALISIS LOGIKA INTI ---
        analysis_logger.info(f"CELERY WORKER: Menjalankan run_full_analysis untuk {username}")
        result = run_full_analysis(processed_csv_path, user_id, username)
        analysis_logger.info("CELERY WORKER: Analisis logika selesai.")

        # --- LANGKAH B: GENERATE LAPORAN PANJANG ---
        analysis_logger.info("CELERY WORKER: Memulai pembuatan laporan panjang...")
        # (Logika ini tetap sama)
        ALLOWED_PERSONALITIES = {"Openess", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"}
        ALLOWED_COGNITIVE_KEYS = {"Kraepelin Test (Numerik)", "WCST (Logika)", "Digit Span (Short Term Memory)"}
        cognitive_key_map = { "KRAEPELIN TEST": "Kraepelin Test (Numerik)", "WCST": "WCST (Logika)", "DIGIT SPAN": "Digit Span (Short Term Memory)" }
        cognitive_db_name_map = {"KRAEPELIN TEST": "Kraepelin", "WCST": "WCST", "DIGIT SPAN": "Digit Span"}

        top_personality_data = max(result['big_five'], key=lambda x: x.get('SCORE', 0))
        top_cognitive_data = max(result['cognitive_function'], key=lambda x: x.get('SCORE', 0))
        tipe_kepribadian_tertinggi = top_personality_data['PERSONALITY'].title()
        kognitif_nama_tertinggi = top_cognitive_data['TEST']
        kognitif_utama_key = cognitive_key_map.get(kognitif_nama_tertinggi.upper())

        output_dir_topoplot = "static/topoplots"
        topoplot_path_behavior = os.path.join(output_dir_topoplot, f"{username}_topoplot_{top_personality_data['PERSONALITY'].lower().replace(' ', '_')}.png")
        topoplot_path_cognitive = os.path.join(output_dir_topoplot, f"{username}_topoplot_{kognitif_nama_tertinggi.lower().replace(' ', '_')}.png")

        biodata_kandidat = {
            "Nama": user.fullname, "Jenis kelamin": user.gender, "Usia": f"{user.age} Tahun",
            "Alamat": user.address, "Keperluan Test": "Profiling dengan Brain Wave Analysis response",
            "Tanggal Test": user.test_date.strftime('%d %B %Y') if user.test_date else "-",
            "Tempat Test": user.test_location, "Operator": user.operator
        }

        output_dir = "static/long_report"
        os.makedirs(output_dir, exist_ok=True)
        nama_file_output_panjang = f"{output_dir}/{username}_long_report.pdf"

        person_job_fit_text, suitability_level_from_long_report = generate_full_report(
            tipe_kepribadian=tipe_kepribadian_tertinggi, kognitif_utama_key=kognitif_utama_key, pekerjaan=pekerjaan,
            model_ai="llama3.1:8b", nama_file_output=nama_file_output_panjang, biodata_kandidat=biodata_kandidat,
            topoplot_path_behaviour=topoplot_path_behavior, topoplot_path_cognitive=topoplot_path_cognitive
        )
        user.laporan_panjang = nama_file_output_panjang
        db.commit()
        analysis_logger.info(f"CELERY WORKER: Laporan panjang selesai. Level kesesuaian: '{suitability_level_from_long_report}'")

        # --- LANGKAH C: GENERATE LAPORAN PENDEK ---
        analysis_logger.info("CELERY WORKER: Memulai pembuatan laporan pendek...")
        personality_details = db.query(models.Personality).filter(models.Personality.name == tipe_kepribadian_tertinggi).first()
        cognitive_db_name = cognitive_db_name_map.get(kognitif_nama_tertinggi.upper())
        cognitive_details = db.query(models.Test).filter(models.Test.name == cognitive_db_name).first()

        output_dir_pendek = "static/short_report"
        os.makedirs(output_dir_pendek, exist_ok=True)
        nama_file_output_pendek = f"{output_dir_pendek}/{username}_short_report.pdf"

        generate_short_report(
            tipe_kepribadian=tipe_kepribadian_tertinggi, kognitif_utama_key=kognitif_utama_key, pekerjaan=pekerjaan,
            model_ai="llama3.1:8b", nama_file_output=nama_file_output_pendek, biodata_kandidat=biodata_kandidat,
            topoplot_path_behaviour=topoplot_path_behavior, topoplot_path_cognitive=topoplot_path_cognitive,
            personality_title=personality_details.title, personality_desc=personality_details.description,
            cognitive_title=cognitive_details.title, cognitive_desc=cognitive_details.description,
            person_job_fit_text_from_long_report=person_job_fit_text,
            suitability_level=suitability_level_from_long_report  # <-- Parameter baru ditambahkan di sini
        )
        user.laporan_pendek = nama_file_output_pendek
        db.commit()
        analysis_logger.info("CELERY WORKER: Laporan pendek selesai.")

    except Exception as e:
        # 3. JIKA TERJADI ERROR DI BLOK TRY, TANGKAP DAN CATAT KE DATABASE
        error_details = traceback.format_exc()
        analysis_logger.error(f"CELERY WORKER ERROR: Terjadi kesalahan fatal saat memproses user {username}: {error_details}")
        if user:
            try:
                user.is_error = True
                user.error_message = f"Error: {e}\n\nTraceback:\n{error_details}"
                db.commit()
                analysis_logger.info(f"Status error untuk user {username} berhasil dicatat ke database.")
            except Exception as db_error:
                analysis_logger.error(f"FATAL: Gagal mencatat status error ke database untuk user {username}. DB Error: {db_error}")
                db.rollback()
    
    finally:
        # --- LANGKAH D: BERSIHKAN FILE SEMENTARA ---
        analysis_logger.info("CELERY WORKER: Membersihkan file sementara...")
        if os.path.exists(processed_csv_path):
            os.remove(processed_csv_path)
        for temp_file in ["cleaning.csv", "cleaning2.csv"]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        db.close()
        analysis_logger.info("CELERY WORKER: Pembersihan selesai.")