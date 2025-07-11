from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uuid
import os

from logic import run_full_analysis, create_user_and_return_id
from database import get_db  # get_db kalau kamu tetap pakai SQLAlchemy session

app = FastAPI()

# Middleware CORS
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
    db: Session = Depends(get_db)  # kalau kamu mau pakai SQLAlchemy
):
    # 1. Simpan file CSV ke lokal
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(".", filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # 2. Simpan data user ke database
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

    try:
        user_id = create_user_and_return_id(user_data)

        # 3. Jalankan analisis EEG
        result = run_full_analysis(file_path, user_id)

        return {
            "message": "User created and analysis completed successfully",
            "user_id": user_id,
            "results": result
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        # 4. Hapus file sementara
        if os.path.exists(file_path):
            os.remove(file_path)
        for temp in ["cleaning.csv", "cleaning2.csv"]:
            if os.path.exists(temp):
                os.remove(temp)
