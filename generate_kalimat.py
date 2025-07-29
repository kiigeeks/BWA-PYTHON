import requests
import json

def generate_with_context(bank_data, prompt_user,tipe_kepribadian="conscientiousness", pekerjaan="Supervisor dan Tax Accounting",model="deepseek-llm"):
    # Buat prompt yang lebih sederhana dan jelas untuk model
    full_prompt = f"""Data referensi:
{bank_data}

Tugas: {prompt_user}

PENTING: Ikuti format ini, tapi boleh tambahkan detail sesuai konteks
"Hasil response EEG menunjukan response interest dan engagement pada stimulus {tipe_kepribadian}. Hasil response menunjukan interest dan engagement pada working memory. Tipe kepribadian {tipe_kepribadian} sangat sesuai untuk posisi {pekerjaan} karena [alasan berdasarkan data]. [Lanjutkan dengan penjelasan detail berdasarkan data referensi]."

Jawab berdasarkan data referensi di atas:"""

    try:
        print("Mengirim request ke model DeepSeek...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Sangat rendah untuk konsistensi
                    "top_p": 0.8,
                    "num_predict": 1000,  # Cukup untuk 1 paragraf
                    "repeat_penalty": 1.2,
                    "stop": ["Data referensi:", "Tugas:", "PENTING:"]
                }
            },
            timeout=120  # Timeout lebih lama
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "").strip()
            
            # Bersihkan output dari artifacts yang tidak perlu
            if generated_text:
                # Hapus bagian yang bukan executive summary
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

# Load data dari file
try:
    with open("bank_data.txt", "r", encoding="utf-8") as f:
        bank_data = f.read()
    print(f"Data berhasil dimuat: {len(bank_data)} karakter")
except FileNotFoundError:
    print("Error: bank_data.txt tidak ditemukan!")
    bank_data = ""

# Input prompt dari user
prompt_user = """
Buatkan sebuah EXECUTIVE SUMMARY profesional dalam bahasa Indonesia dalam 1 paragraf yang menjelaskan:

1. Hasil response EEG terhadap stimulus conscientiousness (interest dan engagement)
2. Hasil response EEG terhadap working memory  
3. Penjelasan mengapa kepribadian conscientiousness cocok untuk posisi Supervisor Tax and Accounting
4. Karakteristik conscientiousness (detail-oriented, sistematis, mengikuti aturan)
5. Relevansi dengan tugas akuntansi dan pajak
6. Person-job fit dan dampak terhadap efektivitas kerja

Gunakan gaya bahasa laporan psikologi industri yang profesional. Berdasarkan data referensi yang diberikan.
"""

print("=== Memulai Generate Executive Summary ===")
hasil = generate_with_context(bank_data, prompt_user)

print("\n===Executive Summary ===\n")
print(hasil)
