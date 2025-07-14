from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from auth import get_password_hash # <- 1. Import fungsi untuk hash password

# ==============================================================================
#  DATA MASTER YANG AKAN DI-INSERT
# ==============================================================================

# --- Data untuk tabel 'tests' ---
TEST_DATA = [
    {"name": "Kraepelin", "title": "Ingatan Kerja Kuat", "description": "Punya kemampuan bagus untuk menyimpan dan mengolah informasi secara cepat di pikiran"},
    {"name": "WCST", "title": "Logika Kuat", "description": "Kemampuan menganalisis data/info dengan baik dan efisien dalam menyelesaikan tantangan"},
    {"name": "Digit Span", "title": "Ingatan Jangka Pendek Kuat", "description": "Mampu menangkap banyak info sekaligus dalam waktu singkat, sehingga pandai mengambil keputusan cepat atau tangkap instruksi kompleks"},
]

# --- Data untuk tabel 'personalities' ---
PERSONALITY_DATA = [
    {"name": "Openess", "title": "Keterbukaan terhadap Pengalaman Baru", "description": "Kreatif: punya banyak ide unik & solusi " + '"out of the box"' + ", suka mencoba hal baru,", "explanation": "X memiliki kecenderungann untuk terbuka terhadap aspek penalaran dan seni. Selain itu ia juga cenderung kreatif dan memiliki ketertarikan terhadap banyak hal"},
    {"name": "Conscientiousness", "title": "Kecenderungan Teliti & Disiplin", "description": "Rapi & terorganisir dalam bekerja, bisa diandalkan untuk tugas detail, rajin dan konsisten menyelesaikan pekerjaan", "explanation": "X memiliki kecenderungan terhadap keteraturan dalam mengerjakan tugas. Selain itu X juga cenderung tekun dan terorganisir dalam bekerja"},
    {"name": "Extraversion", "title": "Kepribadian sosial dan energik", "description": "Cenderung menikmati interaksi sosial dan merasa nyaman dalam situasi yang melibatkan banyak orang", "explanation": "X merupakan orang dengan preferensi untuk aktif dan energetik secara sosial, Tidak jarang juga jika ia suka untuk berbicara dan nyaman bekerja dalam kelompok"},
    {"name": "Agreeableness", "title": "Sifat Mudah Akur & Peduli", "description": "Pribadi yang sangat pengertian, empatik, suka menolong, dan mudah bekerjasama", "explanation": "X merupakan orang dengan kecenderungan untuk dikenal baik karena kehangatan dan keramahannya terhadap sesame. Tak jarang ia juga dikenal kooperatif."},
    {"name": "Neuroticism", "title": "Kecenderungan Emosi Kuat", "description": "Sangat responsif terhadap hal-hal yang memicu emosi negatif(seperti rasa khawatir, takut, atau frustasi)", "explanation": "X adalah orang yang memilki tendensi stabilitas emosional yang tidak terlalu baikdan terkadang mungkin mencemaskan beberapa hal. Tidak jarang ia juga dikenal orang yang sensitif"},
]

# --- Data untuk tabel 'stimulations' ---
STIMULATION_DATA = [
    {"name": "Open Eyes", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Closed Eyes", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Autobiography", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Openess", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Conscientiousness", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Extraversion", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Agreeableness", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Neuroticism", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Kraepelin", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "WCST", "title_graph": "Cognitive Function Test - Digit Span"},
    {"name": "Digit Span", "title_graph": "Cognitive Function Test - Digit Span"},
]

# --- 2. Data untuk Akun Admin ---
ADMIN_USER_DATA = [
    {
        "fullname": "Admin Utama",
        "username": "admin",
        "password": "password123",
        "roles": "admin"
    },
    {
        "fullname": "Admin Cadangan",
        "username": "admin2",
        "password": "password456",
        "roles": "admin"
    }
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

        # --- 3. Proses insert untuk Admin ---
        print("\n🌱 Memasukkan data admin ke tabel 'users'...")
        for data in ADMIN_USER_DATA:
            exists = db.query(models.User).filter_by(username=data["username"]).first()
            if not exists:
                # Hash password sebelum disimpan
                hashed_password = get_password_hash(data["password"])
                admin_user = models.User(
                    fullname=data["fullname"],
                    username=data["username"],
                    password=hashed_password, # Gunakan password yang sudah di-hash
                    roles=data["roles"]
                )
                db.add(admin_user)
        db.commit()
        print("✅ Data admin berhasil dimasukkan.")
        
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