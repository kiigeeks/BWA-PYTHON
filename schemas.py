from pydantic import BaseModel
from typing import Optional, List
import datetime

# ==================================
# SKEMA UNTUK DATA RELASI (NESTED)
# ==================================

class UserPersonality(BaseModel):
    engagement: Optional[float] = None
    excitement: Optional[float] = None
    interest: Optional[float] = None
    score: Optional[float] = None
    brain_topography: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserPersonalityAccuracy(BaseModel):
    AF3: Optional[float] = None
    T7: Optional[float] = None
    Pz: Optional[float] = None
    T8: Optional[float] = None
    AF4: Optional[float] = None
    average: Optional[float] = None

    class Config:
        from_attributes = True

class UserCognitive(BaseModel):
    engagement: Optional[float] = None
    excitement: Optional[float] = None
    interest: Optional[float] = None
    score: Optional[float] = None
    brain_topography: Optional[str] = None

    class Config:
        from_attributes = True

class UserSplitBrain(BaseModel):
    left: Optional[float] = None
    right: Optional[float] = None

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    attention: Optional[float] = None
    stress: Optional[float] = None
    relax: Optional[float] = None
    focus: Optional[float] = None
    graph: Optional[str] = None

    class Config:
        from_attributes = True
        
class FitJob(BaseModel):
    label: Optional[str] = None
    reason: Optional[str] = None
    
    class Config:
        from_attributes = True

class Develop(BaseModel):
    reason: Optional[str] = None
    
    class Config:
        from_attributes = True

class Privilege(BaseModel):
    reason: Optional[str] = None
    
    class Config:
        from_attributes = True

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

    # Menambahkan list dari skema relasi di atas
    personalities_data: List[UserPersonality] = []
    personality_accuracies: List[UserPersonalityAccuracy] = []
    cognitive_data: List[UserCognitive] = []
    split_brain_data: List[UserSplitBrain] = []
    response_data: List[UserResponse] = []
    fit_jobs: List[FitJob] = []
    develops: List[Develop] = []
    privileges: List[Privilege] = []

    class Config:
        from_attributes = True