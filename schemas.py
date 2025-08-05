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
# ==================================

class UserPersonality(BaseModel):
    engagement: Optional[float] = None
    excitement: Optional[float] = None
    interest: Optional[float] = None
    score: Optional[float] = None
    brain_topography: Optional[str] = None
    class Config: from_attributes = True

class UserPersonalityAccuracy(BaseModel):
    AF3: Optional[float] = None
    T7: Optional[float] = None
    Pz: Optional[float] = None
    T8: Optional[float] = None
    AF4: Optional[float] = None
    average: Optional[float] = None
    class Config: from_attributes = True

class UserCognitive(BaseModel):
    engagement: Optional[float] = None
    excitement: Optional[float] = None
    interest: Optional[float] = None
    score: Optional[float] = None
    brain_topography: Optional[str] = None
    class Config: from_attributes = True

class UserSplitBrain(BaseModel):
    left: Optional[float] = None
    right: Optional[float] = None
    class Config: from_attributes = True

class UserResponse(BaseModel):
    attention: Optional[float] = None
    stress: Optional[float] = None
    relax: Optional[float] = None
    focus: Optional[float] = None
    class Config: from_attributes = True

class ROCCurve(BaseModel):
    graph: str
    note: Optional[str] = None
    class Config: from_attributes = True

# ==================================
# SKEMA UTAMA USER (DENGAN RELASI)
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
    conclusions: Optional[str] = None
    report: Optional[str] = None
    jobs: Optional[str] = None
    note_jobs: Optional[str] = None
    laporan_panjang: Optional[str] = None
    laporan_pendek: Optional[str] = None

    personalities_data: List[UserPersonality] = []
    personality_accuracies: List[UserPersonalityAccuracy] = []
    cognitive_data: List[UserCognitive] = []
    split_brain_data: List[UserSplitBrain] = []
    response_data: List[UserResponse] = []
    roc_curves: List[ROCCurve] = []

    class Config:
        from_attributes = True

# ==================================
# SKEMA UNTUK HASIL ANALISIS
# ==================================
class AnalysisBigFive(BaseModel):
    PERSONALITY: str
    ENGAGEMENT: float
    EXCITEMENT: float
    INTEREST: float
    SCORE: float
    BRIEF_EXPLANATION: str

class AnalysisCognitive(BaseModel):
    TEST: str
    ENGAGEMENT: float
    EXCITEMENT: float
    INTEREST: float
    SCORE: float

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

class AnalysisResponse(BaseModel):
    CATEGORY: str
    ATTENTION: float
    STRESS: float
    RELAX: float
    FOCUS: float

class AnalysisResult(BaseModel):
    big_five: List[AnalysisBigFive]
    cognitive_function: List[AnalysisCognitive]
    split_brain: List[AnalysisSplitBrain]
    personality_accuracy: List[AnalysisPersonalityAccuracy]
    response_during_test: List[AnalysisResponse]
    topoplot_urls: dict[str, str]
    roc_curve_urls: dict[str, str]
    long_report_url: Optional[str] = None
    short_report_url: Optional[str] = None

class FilePathPayload(BaseModel):
    file_path: str = Field(..., description="Path ke file CSV yang dihasilkan")