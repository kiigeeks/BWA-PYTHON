import requests
import json

# Ganti tipe kepribadian ini sesuai kebutuhan (misal: "openness", "neuroticism", dll)
tipe_kepribadian = "Agreeableness"

def generate_rekomendasi_karir(bank_data, tipe_kepribadian, model="deepseek-llm"):
    prompt_user = f"""
Anda adalah seorang analis psikologi industri dan organisasi. Tugas Anda adalah merekomendasikan 5 bidang kerja yang relevan untuk individu dengan kepribadian **{tipe_kepribadian}**, serta memberikan alasan berbasis data dan karakteristik psikologis.

Gunakan gaya bahasa laporan profesional berbasis psikologi industri.

### Format Jawaban Wajib:

- Buka dengan paragraf narasi pembuka (1 paragraf) yang menjelaskan mengapa kepribadian {tipe_kepribadian} relevan untuk bidang pekerjaan tertentu.
- Lanjutkan dengan daftar 5 bidang kerja. Untuk setiap bidang kerja:
  - Tulis nama bidang kerja (misal: "1. Sales and Account Management")
  - Tambahkan subbidang jabatan di bawahnya (misal: "Sales Executive, Account Manager, dsb.")
  - Lanjutkan dengan **1 paragraf penjelasan alasan** mengapa kepribadian {tipe_kepribadian} cocok untuk bidang tersebut, khususnya kaitan antara karakteristik kepribadian dan tuntutan pekerjaan.
- Gunakan penomoran angka (1–5) dan **bukan bullet point atau heading**.
- Jangan menambahkan kesimpulan atau penutup.

### Contoh Format Wajib:
Individu dengan kepribadian extraversion dan kemampuan digit span yang tinggi akan optimal dalam pekerjaan yang membutuhkan interaksi sosial yang intensif, pengelolaan informasi numerik, dan kemampuan mengingat informasi angka dengan cepat. Berikut adalah beberapa bidang kerja yang sesuai:  
1. Sales and Account Management  
Sales Executive, Account Manager, Business Development Representative.  
Pekerjaan ini menuntut kemampuan untuk mengingat data klien, target penjualan, dan angka-angka penting lainnya saat berinteraksi dengan klien. Kemampuan digit span yang tinggi akan membantu mereka dalam mengingat informasi numerik terkait kuota penjualan atau anggaran.

### Sekarang tugas Anda:
Buat output seperti format dan gaya di atas, tapi sesuaikan dengan kepribadian **{tipe_kepribadian}**.
Tuliskan hanya 5 bidang kerja dan penjelasan lengkap seperti contoh.
"""


    full_prompt = f"""Data referensi:
{bank_data}

Tugas: {prompt_user}
"""

    try:
        print(f"Mengirim request ke model DeepSeek untuk tipe kepribadian: {tipe_kepribadian}...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "num_predict": 2000,
                    "repeat_penalty": 1.1,
                    "stop": ["Data referensi:", "Tugas:", "PENTING:"]
                }
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "").strip()
            if generated_text:
                lines = generated_text.split('\n')
                clean_lines = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith(('Data referensi:', 'Tugas:', 'PENTING:', '---')):
                        clean_lines.append(line)
                return ' '.join(clean_lines)
            else:
                return "Error: Model tidak menghasilkan response"
        else:
            return f"Error: HTTP {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        return "Error: Model timeout - coba jalankan ulang atau restart ollama serve"
    except requests.exceptions.ConnectionError:
        return "Error: Tidak bisa connect ke Ollama server. Pastikan 'ollama serve' sudah jalan"
    except Exception as e:
        return f"Error: {str(e)}"

# Load data referensi
try:
    with open("bank_data.txt", "r", encoding="utf-8") as f:
        bank_data = f.read()
    print(f"Data berhasil dimuat: {len(bank_data)} karakter")
except FileNotFoundError:
    print("Error: bank_data.txt tidak ditemukan!")
    bank_data = ""

# Jalankan bagian rekomendasi karier
print("=== Memulai Generate Rekomendasi Karier ===")
hasil_karir = generate_rekomendasi_karir(bank_data, tipe_kepribadian)

print("\n=== Rekomendasi Karier ===\n")
print(hasil_karir)
