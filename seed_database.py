from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

# ==============================================================================
#  DATA MASTER YANG AKAN DI-INSERT
# ==============================================================================

# --- Data untuk tabel 'tests' ---
TEST_DATA = [
    {"name": "Kraeplin"},
    {"name": "WSCT"},
    {"name": "Digit_Span"},
]

# --- Data untuk tabel 'personalities' ---
PERSONALITY_DATA = [
    {"name": "Openess", "title": "Keterbukaan terhadap Pengalaman Baru", "description": "Kreatif: punya banyak ide unit & solusi" + '"out of the box"' + ""},
    {"name": "Conscientiousness"},
    {"name": "Extraversion"},
    {"name": "Agreeableness"},
    {"name": "Neuroticism"},
]

# --- Data untuk tabel 'stimulations' ---
STIMULATION_DATA = [
    {"name": "Open_Eyes", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Closed_Eyes", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Autobiography", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Openess", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Conscientiousness", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Extraversion", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Agreeableness", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Neuroticism", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Kraeplin", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "WSCT", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Digit_Span", "title_graph": "Cognitive Function Test - Digit Span"},
]


# ==============================================================================
#  FUNGSI UNTUK MENJALANKAN INSERT
# ==============================================================================

def seed_data():
    """Fungsi utama untuk memasukkan semua data master ke database."""
    db: Session = SessionLocal()
    
    try:
        # --- Proses insert untuk tabel Test ---
        print("🌱 Memasukkan data ke tabel 'tests'...")
        for data in TEST_DATA:
            # Cek apakah data sudah ada
            exists = db.query(models.Test).filter_by(name=data["name"]).first()
            if not exists:
                db.add(models.Test(**data))
        db.commit()
        print("✅ Data 'tests' berhasil dimasukkan.")

        # --- Proses insert untuk tabel Personality ---
        print("\n🌱 Memasukkan data ke tabel 'personalities'...")
        for data in PERSONALITY_DATA:
            exists = db.query(models.Personality).filter_by(name=data["name"]).first()
            if not exists:
                db.add(models.Personality(**data))
        db.commit()
        print("✅ Data 'personalities' berhasil dimasukkan.")

        # --- Proses insert untuk tabel Stimulation ---
        print("\n🌱 Memasukkan data ke tabel 'stimulations'...")
        for data in STIMULATION_DATA:
            exists = db.query(models.Stimulation).filter_by(name=data["name"]).first()
            if not exists:
                db.add(models.Stimulation(**data))
        db.commit()
        print("✅ Data 'stimulations' berhasil dimasukkan.")
        
        print("\n🎉 Semua data master berhasil di-seed ke database.")

    except Exception as e:
        print(f"❌ Terjadi error saat seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Pertama, pastikan tabel sudah dibuat
    print("Memastikan semua tabel sudah ada...")
    models.Base.metadata.create_all(bind=engine)
    print("Pengecekan tabel selesai.")
    
    # Jalankan fungsi seeding
    seed_data()