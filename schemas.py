# filename: schemas.py

from pydantic import BaseModel, Field
from typing import Optional, List, TypeVar, Generic
import datetime

PayloadType = TypeVar('PayloadType')

class StandardResponse(BaseModel, Generic[PayloadType]):
    message: str
    payload: Optional[PayloadType] = None

class TokenPayload(BaseModel):
    access_token: str
    token_type: str

# ==================================
# SKEMA UNTUK DATA RELASI (NESTED)
# (Tidak ada perubahan di bagian ini)
# ==================================

class UserPersonality(BaseModel):
    score: Optional[float] = None
    brain_topography: Optional[str] = None
    class Config: from_attributes = True

class UserCognitive(BaseModel):
    score: Optional[float] = None
    brain_topography: Optional[str] = None
    class Config: from_attributes = True

class UserResponse(BaseModel):
    engagement: Optional[float] = None
    interest: Optional[float] = None
    focus: Optional[float] = None
    relaxation: Optional[float] = None
    attention: Optional[float] = None
    class Config: from_attributes = True

class ROCCurve(BaseModel):
    graph: str
    note: Optional[str] = None
    class Config: from_attributes = True

# ==================================
# SKEMA UTAMA USER (DENGAN RELASI)
# (Tidak ada perubahan di bagian ini)
# ==================================

class User(BaseModel):
    id: int
    fullname: str
    username: str
    company: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    address: Optional[str] = None
    test_date: Optional[datetime.date] = None
    test_location: Optional[str] = None
    roles: Optional[str] = None
    jobs: Optional[str] = None
    laporan_panjang: Optional[str] = None
    laporan_pendek: Optional[str] = None

    personalities_data: List[UserPersonality] = []
    cognitive_data: List[UserCognitive] = []
    response_data: List[UserResponse] = []
    roc_curves: List[ROCCurve] = []

    class Config:
        from_attributes = True

# ==================================
# ### PERUBAHAN DIMULAI DI SINI ###
# SKEMA UNTUK HASIL ANALISIS
# ==================================

# Skema diubah agar cocok dengan output baru dari logic.py
class AnalysisBigFive(BaseModel):
    PERSONALITY: str
    SCORE: float
    BRIEF_EXPLANATION: str
    # engagement, excitement, interest dihapus

# Skema ini masih menggunakan struktur lama karena Bagian 3 belum diimplementasi
class AnalysisCognitive(BaseModel):
    TEST: str
    ENGAGEMENT: float
    EXCITEMENT: float
    INTEREST: float
    SCORE: float

# Skema ini tidak lagi menjadi bagian dari respons utama, jadi tidak perlu diubah
# Namun, akan dihapus dari AnalysisResult
class AnalysisSplitBrain(BaseModel):
    TEST: str
    LEFT_HEMISPHERE: float
    RIGHT_HEMISPHERE: float

class AnalysisPersonalityAccuracy(BaseModel):
    PERSONALITY: str
    AF3: float
    T7: float
    Pz: float
    T8: float
    AF4: float
    AVERAGE: float

# Skema diubah agar cocok dengan output baru dari logic.py
class AnalysisResponse(BaseModel):
    CATEGORY: str
    # Kolom disesuaikan dengan perubahan DB dan logic.py
    ENGAGEMENT: float
    INTEREST: float
    FOCUS: float
    RELAXATION: float
    ATTENTION: float
    # stress dan relax dihapus

# Skema diubah untuk menghapus field yang sudah tidak ada
class AnalysisResult(BaseModel):
    big_five: List[AnalysisBigFive]
    cognitive_function: List[AnalysisCognitive]
    response_during_test: List[AnalysisResponse]
    topoplot_urls: dict[str, str]
    roc_curve_urls: dict[str, str]
    long_report_url: Optional[str] = None
    short_report_url: Optional[str] = None
    # split_brain dan personality_accuracy dihapus dari sini

class FilePathPayload(BaseModel):
    file_path: str = Field(..., description="Path ke file CSV yang dihasilkan")