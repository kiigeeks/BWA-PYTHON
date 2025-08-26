# filename: tasks.py

from celery import Celery
import os
import shutil

# Impor fungsi-fungsi utama dari file lain
from logic import run_full_analysis
from generate_fix import generate_full_report
from generate_fix_pendek import generate_short_report
from database import SessionLocal
import models
from config import settings
from logger_config import setup_logger

# 1. Inisialisasi Celery
#    Ganti 'redis://localhost:6379/0' jika Redis Anda berjalan di lokasi lain.
celery_app = Celery('tasks', broker='redis://localhost:6379/0')
analysis_logger = setup_logger('analysis_logger', 'analysis.log')

# 2. Definisikan tugas latar belakang
@celery_app.task
def process_analysis_task(
    processed_csv_path, user_id, username, pekerjaan
):
    """
    Fungsi ini akan dijalankan oleh Celery di latar belakang.
    Isinya adalah semua proses yang memakan waktu lama.
    """
    analysis_logger.info(f"CELERY WORKER: Memulai analisis untuk user ID {user_id}...")
    db = SessionLocal()
    try:
        # --- LANGKAH A: JALANKAN ANALISIS LOGIKA INTI ---
        analysis_logger.info(f"CELERY WORKER: Menjalankan run_full_analysis untuk {username}")
        result = run_full_analysis(processed_csv_path, user_id, username)
        analysis_logger.info("CELERY WORKER: Analisis logika selesai.")

        # --- LANGKAH B: GENERATE LAPORAN PANJANG ---
        analysis_logger.info("CELERY WORKER: Memulai pembuatan laporan panjang...")
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

        output_dir_topoplot = "static/topoplots"
        topoplot_path_behavior = os.path.join(output_dir_topoplot, f"{username}_topoplot_{top_personality_data['PERSONALITY'].lower().replace(' ', '_')}.png")
        topoplot_path_cognitive = os.path.join(output_dir_topoplot, f"{username}_topoplot_{kognitif_nama_tertinggi.lower().replace(' ', '_')}.png")

        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise ValueError(f"User dengan ID {user_id} tidak ditemukan.")

        biodata_kandidat = {
            "Nama": user.fullname, "Jenis kelamin": user.gender, "Usia": f"{user.age} Tahun",
            "Alamat": user.address, "Keperluan Test": "Profiling dengan Brain Wave Analysis response",
            "Tanggal Test": user.test_date.strftime('%d %B %Y') if user.test_date else "-",
            "Tempat Test": user.test_location, "Operator": user.operator
        }

        output_dir = "static/long_report"
        os.makedirs(output_dir, exist_ok=True)
        nama_file_output_panjang = f"{output_dir}/{username}_long_report.pdf"

        person_job_fit_text = generate_full_report(
            tipe_kepribadian=tipe_kepribadian_tertinggi, kognitif_utama_key=kognitif_utama_key, pekerjaan=pekerjaan,
            model_ai="llama3.1:8b", nama_file_output=nama_file_output_panjang, biodata_kandidat=biodata_kandidat,
            topoplot_path_behaviour=topoplot_path_behavior, topoplot_path_cognitive=topoplot_path_cognitive
        )
        user.laporan_panjang = nama_file_output_panjang
        db.commit()
        analysis_logger.info("CELERY WORKER: Laporan panjang selesai.")

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
            person_job_fit_text_from_long_report=person_job_fit_text
        )
        user.laporan_pendek = nama_file_output_pendek
        db.commit()
        analysis_logger.info("CELERY WORKER: Laporan pendek selesai.")
        
        analysis_logger.info(f"CELERY WORKER: SEMUA PROSES UNTUK USER {username} SELESAI.")

    except Exception as e:
        analysis_logger.info(f"CELERY WORKER ERROR: Terjadi kesalahan saat memproses user {username}: {e}")
    finally:
        # --- LANGKAH D: BERSIHKAN FILE SEMENTARA ---
        analysis_logger.info("CELERY WORKER: Membersihkan file sementara...")
        if os.path.exists(processed_csv_path):
            os.remove(processed_csv_path)
        for temp_file in ["cleaning.csv", "cleaning2.csv"]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        db.close() # Tutup koneksi database
        analysis_logger.info("CELERY WORKER: Pembersihan selesai.")