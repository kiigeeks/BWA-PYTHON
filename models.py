from sqlalchemy import (
    Column, Integer, String, Text, Enum, Date, Float, Double, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from database import Base, engine

# ==============================================================================
#  1. TABEL UTAMA (CENTRAL TABLE)
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
    operator = Column(String(255), nullable=True)
    roles = Column(Enum('admin', 'user', name='user_roles_enum'), default='user')
    jobs = Column(String(255), nullable=True)
    laporan_panjang = Column(String(255), nullable=True)
    laporan_pendek = Column(String(255), nullable=True)
    is_error = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    personalities_data = relationship("UserPersonality", back_populates="user", cascade="all, delete-orphan")
    cognitive_data = relationship("UserCognitive", back_populates="user", cascade="all, delete-orphan")
    response_data = relationship("UserResponse", back_populates="user", cascade="all, delete-orphan")
    roc_curves = relationship("ROCCurve", back_populates="user", cascade="all, delete-orphan")

# ==============================================================================
#  2. TABEL LOOKUP (MASTER DATA)
# ==============================================================================

class Personality(Base):
    __tablename__ = "personalities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    user_personalities = relationship("UserPersonality", back_populates="personality")

class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    user_cognitive_data = relationship("UserCognitive", back_populates="test")

class Stimulation(Base):
    __tablename__ = "stimulations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    user_response_data = relationship("UserResponse", back_populates="stimulation")

# ==============================================================================
#  3. TABEL TRANSAKSI (HASIL ANALISIS)
# ==============================================================================

class UserPersonality(Base):
    __tablename__ = "user_personalities"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    personality_id = Column(Integer, ForeignKey("personalities.id"), nullable=False)
    score = Column(Float, nullable=True)
    brain_topography = Column(String(255), nullable=True)
    user = relationship("User", back_populates="personalities_data")
    personality = relationship("Personality", back_populates="user_personalities")

class UserCognitive(Base):
    __tablename__ = "user_cognitive"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    score = Column(Float)
    brain_topography = Column(String(255))
    user = relationship("User", back_populates="cognitive_data")
    test = relationship("Test", back_populates="user_cognitive_data")

class UserResponse(Base):
    __tablename__ = "user_response"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stimulation_id = Column(Integer, ForeignKey("stimulations.id"), nullable=False)
    engagement = Column(Double)
    interest = Column(Double)
    focus = Column(Double)
    relaxation = Column(Double)
    attention = Column(Double)
    user = relationship("User", back_populates="response_data")
    stimulation = relationship("Stimulation", back_populates="user_response_data")
    
class ROCCurve(Base):
    __tablename__ = "roc_curves"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    graph = Column(String(255), nullable=False)
    note = Column(Text, nullable=True)
    user = relationship("User", back_populates="roc_curves")

def create_all_tables():
    print("Mencoba membuat tabel...")
    Base.metadata.create_all(bind=engine)
    print("Tabel berhasil dibuat (jika belum ada).")

if __name__ == "__main__":
    create_all_tables()
