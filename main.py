from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uuid
import os
import shutil

from logic import run_full_analysis, create_user_and_return_id
from database import get_db

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze/")
async def analyze_csv(
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
    db: Session = Depends(get_db)
):
    # 1. Simpan data user ke DB dan ambil user_id
    user_data = {
        "fullname": fullname,
        "username": username,
        "password": password,
        "company": company,
        "gender": gender,
        "age": age,
        "address": address,
        "test_date": test_date,
        "test_location": test_location
    }
    user_id = create_user_and_return_id(user_data)

    # 2. Simpan file sementara
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(".", filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # 3. Jalankan analisis utama
        result = run_full_analysis(file_path, user_id, username)
        return result

    except Exception as e:
        return {"error": str(e)}

    finally:
        # 4. Hapus file sementara
        os.remove(file_path)
        for temp_file in ["cleaning.csv", "cleaning2.csv"]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
