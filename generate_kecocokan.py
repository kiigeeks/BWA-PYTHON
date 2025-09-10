import subprocess
import sys
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm


# --------------------------------------------------------------------------
# A: FUNGSI BARU UNTUK MEMBACA BANK DATA DARI FILE
# --------------------------------------------------------------------------
def extract_relevant_data(full_text, keywords):
    """
    Mengekstrak bagian teks yang relevan dari bank_data berdasarkan daftar keyword.
    """
    all_headings = [
        "Openness", "Openess", "Conscientiousness", "Extraversion",
        "Agreeableness", "Neuroticism", "Kraepelin Test (Numerik)",
        "WCST (Logika)", "Digit Span (Short Term Memory)", "EXECUTIVE SUMMARY"
    ]
    full_text = full_text.replace("Openess \n", "Openness\n")

    extracted_chunks = []
    for keyword in keywords:
        try:
            start_index = full_text.index(keyword)
            end_index = len(full_text)
            # Cari heading berikutnya untuk batas section
            for heading in all_headings:
                found_pos = full_text.find(heading, start_index + 1)
                if found_pos != -1:
                    end_index = min(end_index, found_pos)

            chunk = full_text[start_index:end_index].strip()
            extracted_chunks.append(chunk)
        except ValueError:
            print(f"Peringatan: Keyword '{keyword}' tidak ditemukan di bank_data.txt")

    return "\n\n".join(extracted_chunks)

# --------------------------------------------------------------------------
# B: KONFIGURASI
# --------------------------------------------------------------------------
TIPE_KEPRIBADIAN = "Extraversion"
KOGNITIF_UTAMA_KEY = "Digit Span (Short Term Memory)"
PEKERJAAN = "Informatika"
MODEL_AI = "llama3.1:8b"
NAMA_FILE_BANK_DATA = "bank_data.txt"
NAMA_FILE_OUTPUT = "laporan_profiling_lengkap.txt"
NAMA_FILE_PDF = "laporan_profiling.pdf"

def build_prompt(job: str, personality: str, cognitive: str, extracted_info: str) -> str:
    """Membangun prompt yang akan dikirim ke model AI, dengan menyertakan data yang sudah diekstrak."""
    # Gabungkan semua informasi ke dalam prompt
    return f"""
ANDA ADALAH SEORANG AHLI PSIKOLOGI DAN ANALIS KARIER YANG OBJEKTIF DAN MENGIKUTI INSTRUKSI DENGAN TEPAT.
Tugas Anda adalah memberikan analisis yang mendalam dan seimbang. Gunakan informasi ilmiah di bawah ini sebagai referensi utama.

---
INFORMASI PENDUKUNG (REFERENSI)
---

{extracted_info}

---
TUGAS UTAMA ANDA
---

Lakukan analisis kecocokan yang seimbang dan *spesifik* untuk pekerjaan: '{job}'.

Input:
- Pekerjaan: {job}
- Personality: {personality}
- Tes Kognitif: {cognitive}

Ikuti Langkah Ini Dengan Tepat:
1.  Tentukan 4-6 kompetensi utama yang *spesifik dan relevan* untuk '{job}'. (DILARANG menggunakan nama generik seperti 'Kompetensi A').
2.  Untuk setiap kompetensi, berikan skor persentase kecocokan (0-100) untuk 'Personality' dan 'Tes Kognitif'.
3.  Hitung rata-rata kesesuaian (%) untuk setiap kompetensi.
4.  Isi kolom 'Interpretasi'. Kolom ini WAJIB dan HANYA BOLEH berisi salah satu dari tiga frasa berikut, berdasarkan nilai rata-rata:
    - *Sangat Sesuai* (jika rata-rata >= 75%)
    - *Sesuai* (jika rata-rata antara 50% - 75%)
    - *Kurang Sesuai* (jika rata-rata < 50%)
5.  Sajikan semua hasil dalam SATU tabel markdown. JANGAN tambahkan penjelasan atau kalimat lain di dalam sel tabel.
6.  Setelah tabel, buat 'Kesimpulan Singkat' dalam format poin-poin (bullet points) seperti contoh. Anda HARUS MENGHITUNG RATA-RATA UMUM dari semua kompetensi.

---
FORMAT OUTPUT AKHIR (IKUTI DENGAN TEPAT)
---

### Analisis Kecocokan untuk: {job}

| Kompetensi Utama | {personality} (%) | {cognitive} (%) | Rata-rata Kesesuaian (%) | Interpretasi |
| :--- | :---: | :---: | :---: | :--- |
| (Nama Kompetensi 1 yang spesifik) | (Skor) | (Skor) | (Rata-rata) | (Sangat Sesuai / Sesuai / Kurang Sesuai) |
| (Nama Kompetensi 2 yang spesifik) | (Skor) | (Skor) | (Rata-rata) | (Sangat Sesuai / Sesuai / Kurang Sesuai) |
| (Nama Kompetensi 3 yang spesifik) | (Skor) | (Skor) | (Rata-rata) | (Sangat Sesuai / Sesuai / Kurang Sesuai) |

---

*Kesimpulan Singkat:*

* *Rata-rata umum kesesuaian:* (Hitung dan tulis rata-rata dari semua kompetensi di tabel dalam format XX,X%)
* *Kategori:* (Tentukan kategori umum berdasarkan rata-rata tersebut, contoh: Sesuai cenderung Sangat Sesuai)
* (Tuliskan satu kalimat tentang kekuatan utama, menghubungkan trait '{personality}' dan '{cognitive}' dengan aspek pekerjaan '{job}')
* (Tuliskan satu kalimat tentang area pengembangan atau potensi kelemahan berdasarkan analisis trait)
"""

def run_llama(prompt: str, model: str = MODEL_AI) -> str:
    try:
        command = ["ollama", "run", model]
        result = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        return result.stdout.strip()
    except FileNotFoundError:
        return "Error: Perintah 'ollama' tidak ditemukan."
    except subprocess.CalledProcessError as e:
        return f"Error saat menjalankan model Ollama:\n{e.stderr}"
    except Exception as e:
        return f"Terjadi error tidak terduga: {e}"

# --------------------------------------------------------------------------
# C: PARSER TABEL MARKDOWN
# --------------------------------------------------------------------------
def parse_markdown_table(table_text: str):
    """
    Parse tabel markdown menjadi list of lists.
    Skip baris separator (---).
    """
    rows = table_text.strip().split("\n")
    parsed = []
    for row in rows:
        if row.strip().startswith("|"):
            parts = [cell.strip() for cell in row.split("|")[1:-1]]
            if all(re.match(r"^:?-{3,}:?$", p) for p in parts):
                continue
            parsed.append(parts)
    return parsed

# --------------------------------------------------------------------------
# D: GENERATE PDF
# --------------------------------------------------------------------------
def generate_pdf(parsed_array, filename):
    print(f"Membuat file PDF '{filename}'...")

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    elements = []

    # Style paragraf untuk wrap teks
    para_style = ParagraphStyle(
        "TableCell",
        fontSize=9,
        leading=11,
        wordWrap="CJK"  # bikin teks auto wrap ke bawah
    )

    # Header tabel pakai Paragraph juga
    headers = [
        Paragraph("Kompetensi Utama", para_style),
        Paragraph("Extraversion (%)", para_style),
        Paragraph("Digit Span (Short Term Memory) (%)", para_style),
        Paragraph("Rata-rata Kesesuaian (%)", para_style),
        Paragraph("Interpretasi", para_style),
    ]

    data = [headers]

    # Isi tabel: bungkus semua cell dengan Paragraph agar bisa wrap
    for row in parsed_array:
        wrapped_row = [Paragraph(str(cell), para_style) for cell in row]
        data.append(wrapped_row)

    # Lebar kolom lebih seimbang
    col_widths = [6*cm, 3*cm, 3.5*cm, 3.5*cm, 4*cm]

    table = Table(data, colWidths=col_widths)

    # Styling tabel
    style = TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),
    ])

    table.setStyle(style)
    elements.append(table)

    doc.build(elements)
 # --------------------------------------------------------------------------
# MAIN PROGRAM
# --------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        print(f"Membaca bank data dari file '{NAMA_FILE_BANK_DATA}'...")
        with open(NAMA_FILE_BANK_DATA, 'r', encoding='utf-8') as f:
            full_bank_data_text = f.read()
    except FileNotFoundError:
        print(f"Error: File bank data '{NAMA_FILE_BANK_DATA}' tidak ditemukan.")
        sys.exit(1)

    print("Mengekstrak data yang relevan dari bank data...")
    keywords_to_find = [TIPE_KEPRIBADIAN, KOGNITIF_UTAMA_KEY]
    extracted_data = extract_relevant_data(full_bank_data_text, keywords_to_find)

    print("Membangun prompt dengan konteks dari Bank Data...")
    prompt = build_prompt(PEKERJAAN, TIPE_KEPRIBADIAN, KOGNITIF_UTAMA_KEY, extracted_data)

    print(f"Menjalankan model '{MODEL_AI}'... (Ini mungkin butuh beberapa saat)")
    output = run_llama(prompt, MODEL_AI)

    # Simpan hasil ke TXT
    with open(NAMA_FILE_OUTPUT, "w", encoding="utf-8") as f:
        f.write("=== PROMPT YANG DIKIRIM ===\n")
        f.write(prompt.strip() + "\n\n")
        f.write("=== HASIL DARI MODEL ===\n")
        f.write(output)
    print(f"Hasil berhasil disimpan ke {NAMA_FILE_OUTPUT}")

    print("\nMem-parsing tabel hasil...")
    parsed_array = parse_markdown_table(output)

    if parsed_array:
        parsed_array = parsed_array[1:]
    
    for row in parsed_array:
        print(row)

    print(f"\nMembuat file PDF '{NAMA_FILE_PDF}'...")
    generate_pdf(parsed_array, NAMA_FILE_PDF)
    print("PDF berhasil dibuat.")