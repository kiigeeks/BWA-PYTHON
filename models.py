# models.py

# Import komponen yang dibutuhkan dari sqlalchemy
from sqlalchemy import (
    Column, Integer, String, Text, Enum, Date, Float, 
    ForeignKey
)
from sqlalchemy.orm import relationship

# PERUBAHAN UTAMA: Impor 'Base' dari file database.py kita, bukan membuatnya di sini.
from database import Base, engine


# ==============================================================================
#  1. TABEL UTAMA (CENTRAl TABLE)
# ==============================================================================

class User(Base):
    """
    Tabel utama yang menyimpan data demografi pengguna/subjek.
    Tabel ini menjadi pusat dari semua data analisis lainnya.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(255), nullable=False)
    username = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    gender = Column(String(50), nullable=True)
    age = Column(Integer, nullable=True)
    address = Column(String(255), nullable=True) 
    test_date = Column(Date, nullable=True)
    test_location = Column(String(255), nullable=True)
    roles = Column(Enum('admin', 'user', name='user_roles_enum'), default='user')
    conclusions = Column(Text, nullable=True)
    report = Column(String(255), nullable=True)
    jobs = Column(String(255), nullable=True)
    note_jobs = Column(String(255), nullable=True)

    # --- RELASI ONE-TO-MANY ---
    personalities_data = relationship("UserPersonality", back_populates="user", cascade="all, delete-orphan")
    personality_accuracies = relationship("UserPersonalityAccuracy", back_populates="user", cascade="all, delete-orphan")
    cognitive_data = relationship("UserCognitive", back_populates="user", cascade="all, delete-orphan")
    split_brain_data = relationship("UserSplitBrain", back_populates="user", cascade="all, delete-orphan")
    response_data = relationship("UserResponse", back_populates="user", cascade="all, delete-orphan")
    fit_jobs = relationship("FitJob", back_populates="user", cascade="all, delete-orphan")
    develops = relationship("Develop", back_populates="user", cascade="all, delete-orphan")
    privileges = relationship("Privilege", back_populates="user", cascade="all, delete-orphan")

# ==============================================================================
#  2. TABEL LOOKUP (MASTER DATA)
# ==============================================================================

class Personality(Base):
    """Tabel master untuk jenis-jenis kepribadian (mis: Openness, etc)."""
    __tablename__ = "personalities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    
    user_personalities = relationship("UserPersonality", back_populates="personality")
    user_accuracy_data = relationship("UserPersonalityAccuracy", back_populates="personality")

class Test(Base):
    """Tabel master untuk jenis-jenis tes kognitif (mis: Kraeplin, WSCT)."""
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    user_cognitive_data = relationship("UserCognitive", back_populates="test")
    user_split_brain_data = relationship("UserSplitBrain", back_populates="test")

class Stimulation(Base):
    """Tabel master untuk jenis-jenis stimulasi (mis: Open Eyes, Closed Eyes)."""
    __tablename__ = "stimulations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    title_graph = Column(String(255), nullable=True)

    user_response_data = relationship("UserResponse", back_populates="stimulation")

# ==============================================================================
#  3. TABEL TRANSAKSI (HASIL ANALISIS)
# ==============================================================================

class UserPersonality(Base):
    """Menyimpan skor hasil tes kepribadian untuk seorang user."""
    __tablename__ = "user_personalities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    personality_id = Column(Integer, ForeignKey("personalities.id"), nullable=False)
    
    engagement = Column(Float, nullable=True)
    excitement = Column(Float, nullable=True)
    interest = Column(Float, nullable=True)
    score = Column(Float, nullable=True)
    brain_topography = Column(String(255), nullable=True)
    
    user = relationship("User", back_populates="personalities_data")
    personality = relationship("Personality", back_populates="user_personalities")

# ... (Kelas UserPersonalityAccuracy, UserCognitive, UserSplitBrain, UserResponse, FitJob, Develop, Privilege tetap sama persis seperti sebelumnya) ...
# (Saya singkat di sini agar tidak terlalu panjang, cukup salin dari kode sebelumnya)

class UserPersonalityAccuracy(Base):
    __tablename__ = "user_personality_accuracies"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    personality_id = Column(Integer, ForeignKey("personalities.id"), nullable=False)
    AF3 = Column(Float)
    T7 = Column(Float)
    Pz = Column(Float)
    T8 = Column(Float)
    AF4 = Column(Float)
    average = Column(Float)
    user = relationship("User", back_populates="personality_accuracies")
    personality = relationship("Personality", back_populates="user_accuracy_data")

class UserCognitive(Base):
    __tablename__ = "user_cognitive"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    engagement = Column(Float)
    excitement = Column(Float)
    interest = Column(Float)
    score = Column(Float)
    brain_topography = Column(String(255))
    user = relationship("User", back_populates="cognitive_data")
    test = relationship("Test", back_populates="user_cognitive_data")

class UserSplitBrain(Base):
    __tablename__ = "user_split_brain"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    left = Column(Float)
    right = Column(Float)
    user = relationship("User", back_populates="split_brain_data")
    test = relationship("Test", back_populates="user_split_brain_data")

class UserResponse(Base):
    __tablename__ = "user_response"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stimulation_id = Column(Integer, ForeignKey("stimulations.id"), nullable=False)
    attention = Column(Float)
    stress = Column(Float)
    relax = Column(Float)
    focus = Column(Float)
    graph = Column(String(255))
    user = relationship("User", back_populates="response_data")
    stimulation = relationship("Stimulation", back_populates="user_response_data")

class FitJob(Base):
    __tablename__ = "fit_jobs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    label = Column(String(255))
    reason = Column(Text)
    user = relationship("User", back_populates="fit_jobs")

class Develop(Base):
    __tablename__ = "develops"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text)
    user = relationship("User", back_populates="develops")

class Privilege(Base):
    __tablename__ = "privileges"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text)
    user = relationship("User", back_populates="privileges")


# --- Fungsi untuk membuat semua tabel di database ---
def create_all_tables():
    """Fungsi ini akan membuat semua tabel yang didefinisikan di atas."""
    print("Mencoba membuat tabel...")
    # Base sudah tahu tentang engine dari file database.py
    Base.metadata.create_all(bind=engine)
    print("Tabel berhasil dibuat (jika belum ada).")

if __name__ == "__main__":
    create_all_tables()