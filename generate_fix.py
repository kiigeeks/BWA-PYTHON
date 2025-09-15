# -*- coding: utf-8 -*-

# ==============================================================================
# BAGIAN 1: IMPORT LIBRARY
# ==============================================================================
import requests
import json
import re
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color, black
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from behavior_traits_data import BEHAVIOR_TRAITS_BANK
from cognitive_traits_data import COGNITIVE_TRAITS_BANK
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import Color, black, lightblue, white, grey, whitesmoke
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER


# ==============================================================================
# BAGIAN 2: KONSTANTA GLOBAL & TEMPLATE
# ==============================================================================
PAGE_WIDTH, PAGE_HEIGHT = A4

class OllamaConnectionError(Exception):
    """Exception khusus untuk menandai error koneksi ke Ollama."""
    pass

# Template Prompt dipindahkan ke scope global agar lebih rapi
PROMPT_TEMPLATES = {
    "prompt_step1_deep_analysis_and_score": """
        Anda adalah seorang ahli psikologi industri dan organisasi (PIO) senior.
        
        TUGAS: Lakukan analisis MENTAH yang sangat detail dalam format poin-poin. JANGAN MENULIS PARAGRAF. Di akhir, berikan penilaian skor mentah dari 1 (sangat tidak sesuai) hingga 10 (sangat sesuai) beserta justifikasinya.
        
        PROFIL KANDIDAT:
        - Kepribadian: {tipe_kepribadian}
        - Kognitif: {kognitif_utama}
        - Konteks Tambahan: {specific_context}
        
        POSISI YANG DITUJU:
        - Jabatan: {pekerjaan}
        
        FORMAT OUTPUT WAJIB:
        1.  **Sinergi Positif:** Jelaskan bagaimana {tipe_kepribadian} dan {kognitif_utama} saling mendukung untuk peran {pekerjaan}.
        2.  **Potensi Konflik/Risiko:** Jelaskan potensi benturan antara profil kandidat dengan tuntutan peran.
        3.  **Rekomendasi Aksi:** Saran pengembangan yang konkret.
        4.  **Penilaian Skor Mentah (1-10):** [Tuliskan skor di sini]
        5.  **Justifikasi Skor:** [Jelaskan secara singkat mengapa Anda memberikan skor tersebut, dengan mempertimbangkan keseimbangan sinergi vs risiko]
        """,

        # LANGKAH 2: PENENTUAN LABEL KESESUAIAN
        "prompt_step2_determine_level": """
        Anda adalah seorang quality control analyst.
        
        TUGAS: Berdasarkan analisis dan skor di bawah, pilih SATU label yang paling sesuai dari tiga opsi berikut: "Sangat Sesuai", "Sesuai dengan Catatan Pengembangan", "Kurang Sesuai".
        
        PANDUAN PEMILIHAN LABEL:
        - Skor 8-10: Pilih "Sangat Sesuai"
        - Skor 5-7: Pilih "Sesuai dengan Catatan Pengembangan"
        - Skor 1-4: Pilih "Kurang Sesuai"
        
        ANALISIS UNTUK DIEVALUASI:
        ---
        {deep_analysis_and_score}
        ---
        
        ATURAN: Output Anda HANYA berupa salah satu dari tiga label tersebut. Jangan menulis apa pun lagi.
        """,

        # LANGKAH 3: PENULISAN NARASI FINAL
        "prompt_step3_write_narrative": """
        Anda adalah seorang penulis laporan psikologi industri senior yang ahli dalam menyusun analisis yang mendalam dan actionable.

        TUGAS: Tulis **DUA PARAGRAF** executive summary yang komprehensif dan profesional berdasarkan analisis mentah dan label kesesuaian yang sudah ditentukan.

        ======================================
        DATA UNTUK DITULIS:
        - Label Kesesuaian yang Telah Ditentukan: "{determined_level}"
        - Analisis Mentah Lengkap:
        ---
        {deep_analysis_and_score}
        ---
        ======================================

        INSTRUKSI PENULISAN WAJIB:

        **Paragraf 1: FOKUS PADA DIAGNOSIS KESESUAIAN**
        1.  Awali dengan menyatakan level kesesuaian yang telah ditentukan (Contoh: "Berdasarkan analisis profil, individu ini dinilai **{determined_level}** untuk posisi...").
        2.  Jelaskan **kekuatan utama** (sinergi positif) yang mendukung penilaian tersebut. Kaitkan langsung dengan tugas-tugas spesifik pada posisi yang dilamar.
        3.  Jelaskan secara **detail dan eksplisit mengenai Potensi Konflik/Risiko**. Uraikan MENGAPA kelemahan tersebut menjadi masalah signifikan untuk peran ini. Jangan hanya menyebutkan kelemahannya, tetapi jelaskan **dampaknya** pada performa kerja.

        **Paragraf 2: FOKUS PADA RENCANA PENGEMBANGAN**
        1.  Awali dengan kalimat transisi yang jelas (Contoh: "Untuk memaksimalkan potensi dan memitigasi risiko tersebut...").
        2.  Berikan **rekomendasi pengembangan yang konkret dan dapat ditindaklanjuti (actionable)** berdasarkan poin "Rekomendasi Aksi" dari analisis mentah.
        3.  Jelaskan bagaimana rekomendasi tersebut dapat membantu individu mengatasi kelemahan yang dibahas di paragraf pertama.
        4.  Akhiri dengan kalimat penutup yang optimis namun realistis mengenai potensi kandidat jika pengembangan dilakukan.

        **ATURAN TAMBAHAN:**
        - Gunakan format bold `**teks**` untuk menyorot istilah-istilah kunci.
        - Jangan sebutkan "skor" atau "nilai" numerik dalam narasi.
        - Pastikan alur antar paragraf logis dan mengalir.
        - OUTPUT HARUS TEPAT DUA PARAGRAF.
        """,
        # --- LANGKAH 1 (BARU): MINTA ANALISIS MENTAH UNTUK PROFIL UMUM ---
        "prompt_general_analysis": """
        Anda adalah seorang psikolog ahli.
        
        TUGAS: Lakukan analisis MENTAH dalam format poin-poin. JANGAN MENULIS PARAGRAF NARATIF. Fokus pada kekuatan dan potensi kelemahan dari kombinasi profil di bawah ini secara umum.
        
        PROFIL KANDIDAT:
        - Kepribadian Dominan: {tipe_kepribadian}
        - Kognitif Dominan: {kognitif_utama}
        - Konteks Tambahan dari Bank Data:
        ---
        {specific_context}
        ---
        
        FORMAT OUTPUT WAJIB:
        1.  **Kekuatan Utama Profil:** Jelaskan bagaimana {tipe_kepribadian} dan {kognitif_utama} menciptakan kekuatan unik pada individu.
        2.  **Potensi Area Pengembangan:** Jelaskan kelemahan atau tantangan yang mungkin muncul dari kombinasi profil ini.
        """,

        # --- LANGKAH 2 (BARU): MINTA PENULISAN NARASI DARI ANALISIS MENTAH ---
        "prompt_general_narrative": """
        Anda adalah seorang penulis laporan psikologi senior yang ahli menyusun ringkasan profil yang jelas dan profesional.

        TUGAS: Tulis **DUA PARAGRAF** executive summary yang mengalir dan mudah dibaca berdasarkan analisis mentah di bawah.
        
        ANALISIS MENTAH UNTUK DITULIS ULANG:
        ---
        {general_analysis_output}
        ---

        INSTRUKSI PENULISAN WAJIB:
        
        **Paragraf 1: FOKUS PADA KEKUATAN PROFIL**
        - Jelaskan karakteristik kepribadian dan kognitif utama kandidat.
        - Uraikan **Kekuatan Utama Profil** dari analisis mentah menjadi sebuah narasi yang mulus. Jelaskan bagaimana kekuatan ini bermanfaat dalam aktivitas umum (belajar, bekerja, interaksi sosial).
        
        **Paragraf 2: FOKUS PADA AREA PENGEMBANGAN**
        - Buat kalimat transisi yang halus (Contoh: "Meskipun memiliki kekuatan tersebut...").
        - Jelaskan **Potensi Area Pengembangan** dari analisis mentah. Uraikan mengapa ini bisa menjadi tantangan bagi individu.
        - Tutup dengan kalimat yang merangkum potensi individu secara keseluruhan.

        **ATURAN MUTLAK:**
        - Jangan gunakan format poin-poin. Semua harus dalam bentuk paragraf naratif.
        - Gunakan format bold `**teks**` untuk menyorot istilah kunci.
        - JANGAN sebutkan "pekerjaan", "posisi", "jabatan", atau "kesesuaian".
        - OUTPUT HARUS TEPAT DUA PARAGRAF.
        """,

        "person_job_fit_full": """
        Anda adalah seorang analis karir ahli. Tugas Anda adalah membuat analisis rekomendasi bidang kerja yang sesuai berdasarkan profil kandidat dengan format yang spesifik dan terstruktur.

        ==============================
        **TEMPLATE FORMAT YANG HARUS DIIKUTI PERSIS:**
        ==============================
        
        Individu dengan kepribadian [KEPRIBADIAN] dan kemampuan [KOGNITIF] akan optimal dalam pekerjaan yang membutuhkan [sebutkan karakteristik kerja yang spesifik sesuai profil]. Berikut adalah beberapa bidang kerja yang sesuai:
        
        **[Nama Kategori Bidang 1]**
        [Job Title 1], [Job Title 2]. [Penjelasan 1-2 kalimat mengapa bidang ini sesuai, bagaimana kepribadian dan kognitif dimanfaatkan dalam pekerjaan tersebut, serta contoh tugas spesifik].
        
        **[Nama Kategori Bidang 2]**  
        [Job Title 1], [Job Title 2]. [Penjelasan 1-2 kalimat mengapa bidang ini sesuai, bagaimana kepribadian dan kognitif dimanfaatkan dalam pekerjaan tersebut, serta contoh tugas spesifik].
        
        **[Nama Kategori Bidang 3]**
        [Job Title 1], [Job Title 2]. [Penjelasan 1-2 kalimat mengapa bidang ini sesuai, bagaimana kepribadian dan kognitif dimanfaatkan dalam pekerjaan tersebut, serta contoh tugas spesifik].
        
        **[Nama Kategori Bidang 4]**
        [Job Title 1], [Job Title 2]. [Penjelasan 1-2 kalimat mengapa bidang ini sesuai, bagaimana kepribadian dan kognitif dimanfaatkan dalam pekerjaan tersebut, serta contoh tugas spesifik].
        
        **[Nama Kategori Bidang 5]**
        [Job Title 1], [Job Title 2]. [Penjelasan 1-2 kalimat mengapa bidang ini sesuai, bagaimana kepribadian dan kognitif dimanfaatkan dalam pekerjaan tersebut, serta contoh tugas spesifik].

        **[Nama Kategori Bidang 6]**
        [Job Title 1], [Job Title 2]. [Penjelasan 1-2 kalimat mengapa bidang ini sesuai, bagaimana kepribadian dan kognitif dimanfaatkan dalam pekerjaan tersebut, serta contoh tugas spesifik].

        **SEKARANG, TUGAS ANDA:**
        Buatlah analisis rekomendasi pekerjaan untuk profil di bawah ini menggunakan format template di atas SECARA PERSIS.

        **PROFIL UNTUK DIANALISIS:**
        - Kepribadian Dominan: {tipe_kepribadian}
        - Kekuatan Kognitif: {kognitif_utama}

        **ATURAN MUTLAK:**
        1. **PARAGRAF PEMBUKA**: Ikuti pola "Individu dengan kepribadian X dan kemampuan Y akan optimal dalam pekerjaan yang membutuhkan..."
        2. **KALIMAT TRANSISI**: Selalu gunakan "Berikut adalah beberapa bidang kerja yang sesuai:"
        3. **FORMAT KATEGORI**: 
        - Gunakan **Nama Kategori** (contoh: **Sales & Account Management**, **Customer Service & Client Relations**)
        - Daftar 2-3 job titles dipisah koma, diakhiri titik
        - Langsung lanjut dengan penjelasan dalam 1 paragraf (1-2 kalimat)
        4. **BERIKAN 5 KATEGORI** bidang kerja yang berbeda dan spesifik
        5. **PENJELASAN SETIAP KATEGORI HARUS**:
        - Menjelaskan mengapa sesuai dengan profil
        - Menyebutkan bagaimana kepribadian digunakan
        - Menyebutkan bagaimana kemampuan kognitif dimanfaatkan
        - Memberikan contoh tugas atau situasi kerja spesifik
        6. **BAHASA**: Gunakan Bahasa Indonesia yang profesional, formal, dan mudah dipahami orang awam
        7. **JANGAN** gunakan bullet points, numbering, atau tag HTML
        8. **KONSISTENSI**: Ikuti format template tanpa variasi apapun
        9. **SPESIFIK**: Semua rekomendasi harus logis dan relevan dengan kombinasi kepribadian + kognitif yang diberikan
     """,
     "prompt_job_suitability_table": """
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
        """
}

# file: generate_fix.py

def generate_executive_summary(pekerjaan, tipe_kepribadian, kognitif_utama, model_ai, bank_data_text, determined_level_from_table=None, average_score_from_table=None):
    """
    Menghasilkan executive summary secara dinamis.
    Jika 'pekerjaan' ada, buat analisis kesesuaian.
    Jika tidak, buat profil psikologis umum.
    """
    # Ekstrak konteks yang relevan dari bank data
    keywords_for_summary = [tipe_kepribadian, kognitif_utama]
    specific_context = extract_relevant_data(bank_data_text, keywords_for_summary)

    final_narrative = "Konten Executive Summary gagal digenerate."

    if pekerjaan:
        # JIKA PEKERJAAN ADA: Lakukan analisis kesesuaian
        print(f"   -> Pekerjaan '{pekerjaan}' terdeteksi. Menjalankan analisis kesesuaian...")
        
        # Langkah 1: Analisis & Skor Mentah
        prompt_step1 = PROMPT_TEMPLATES["prompt_step1_deep_analysis_and_score"].format(
            specific_context=specific_context, tipe_kepribadian=tipe_kepribadian, pekerjaan=pekerjaan, kognitif_utama=kognitif_utama)
        deep_analysis_output = generate_ai_content(prompt_step1, model=model_ai, task_name="ES - Analisis & Skor")
        
        if "Error:" not in deep_analysis_output:
            determined_level = ""
            # --- PERUBAHAN 1: Gunakan level dari tabel jika tersedia ---
            if determined_level_from_table:
                print(f"   -- Level kesesuaian diambil dari rata-rata tabel: '{determined_level_from_table}'")
                determined_level = determined_level_from_table
            else:
                # Jalur fallback: Jika tidak ada data tabel, biarkan AI yang menentukan level
                print("   -- Menentukan level kesesuaian via AI (jalur fallback)...")
                prompt_step2 = PROMPT_TEMPLATES["prompt_step2_determine_level"].format(deep_analysis_and_score=deep_analysis_output)
                determined_level = generate_ai_content(prompt_step2, model=model_ai, task_name="ES - Penentuan Level").strip()
            
            if "Error:" not in determined_level and determined_level:
                # Langkah 3: Penulisan Narasi Final
                prompt_step3 = PROMPT_TEMPLATES["prompt_step3_write_narrative"].format(
                    determined_level=determined_level, deep_analysis_and_score=deep_analysis_output)
                final_narrative = generate_ai_content(prompt_step3, model=model_ai, task_name="ES - Penulisan Narasi")
    else:
        print("   -> Pekerjaan tidak diisi. Menjalankan summary profil umum (2 langkah)...")
        
        prompt_analysis = PROMPT_TEMPLATES["prompt_general_analysis"].format(
            tipe_kepribadian=tipe_kepribadian,
            kognitif_utama=kognitif_utama,
            specific_context=specific_context
        )
        general_analysis_output = generate_ai_content(prompt_analysis, model=model_ai, task_name="ES - Analisis Profil Umum")

        if "Error:" not in general_analysis_output:
            prompt_narrative = PROMPT_TEMPLATES["prompt_general_narrative"].format(
                general_analysis_output=general_analysis_output
            )
            final_narrative = generate_ai_content(prompt_narrative, model=model_ai, task_name="ES - Penulisan Narasi Profil Umum")
        else:
            final_narrative = general_analysis_output

    if determined_level_from_table and average_score_from_table is not None:
        try:
            # Format persentase menjadi string seperti "(61%)"
            percentage_str = f"({average_score_from_table:.0f}%)"

            # Teks target yang akan diganti (dalam format Markdown)
            target_text_md = f"**{determined_level_from_table}**"

            # Teks pengganti yang baru (juga dalam format Markdown)
            replacement_text_md = f"**{determined_level_from_table} {percentage_str}**"

            # Lakukan penggantian pada teks narasi
            # Menggunakan .replace() sederhana sudah cukup dan aman di sini
            final_narrative = final_narrative.replace(target_text_md, replacement_text_md, 1)

        except (ValueError, TypeError):
            # Jika ada error saat format, lewati saja agar program tidak crash
            pass
        
    if "Error:" not in final_narrative:
        final_narrative = final_narrative.replace('**Executive Summary**', '').strip()                  
        return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', final_narrative)
    else:
        return final_narrative
    
# ==============================================================================
# BAGIAN 3: FUNGSI GENERASI KONTEN AI
# (Tidak ada perubahan di bagian ini)
# ==============================================================================
def extract_relevant_data(full_text, keywords):
    """
    Mengekstrak bagian teks yang relevan dari bank_data berdasarkan daftar keyword.
    Versi ini disempurnakan dari generate_kecocokan.py
    """
    all_headings = [
        "Openness", "Openess", "Conscientiousness", "Extraversion",
        "Agreeableness", "Neuroticism", "Kraepelin Test (Numerik)",
        "WCST (Logika)", "Digit Span (Short Term Memory)", "EXECUTIVE SUMMARY"
    ]
    # Koreksi otomatis untuk variasi penulisan "Openess"
    full_text = full_text.replace("Openess \n", "Openness\n")

    extracted_chunks = []
    for keyword in keywords:
        try:
            start_index = full_text.index(keyword)
            end_index = len(full_text)
            for heading in all_headings:
                # Cari heading berikutnya sebagai batas akhir section
                found_pos = full_text.find(heading, start_index + 1)
                if found_pos != -1:
                    end_index = min(end_index, found_pos)
            chunk = full_text[start_index:end_index].strip()
            extracted_chunks.append(chunk)
        except ValueError:
            print(f"Peringatan: Keyword '{keyword}' tidak ditemukan di bank_data.txt")
    return "\n\n".join(extracted_chunks)

def parse_markdown_table(table_text: str):
    """
    Parse tabel markdown menjadi list of lists, mengabaikan baris separator.
    """
    rows = table_text.strip().split("\n")
    parsed = []
    for row in rows:
        if row.strip().startswith("|"):
            parts = [cell.strip() for cell in row.split("|")[1:-1]]
            if all(re.match(r"^:?-{3,}:?$", p) for p in parts):
                continue
            if any(p for p in parts):
                parsed.append(parts)
    if len(parsed) > 1:
        return parsed[1:]
    return []


def generate_suitability_analysis(pekerjaan, tipe_kepribadian, kognitif_utama_key, model_ai, bank_data_text):
    """
    Fungsi terintegrasi untuk menghasilkan data tabel kecocokan pekerjaan.
    """
    print("   -> Memulai analisis kecocokan untuk tabel...")
    keywords = [tipe_kepribadian, kognitif_utama_key]
    extracted_data = extract_relevant_data(bank_data_text, keywords)
    
    prompt = PROMPT_TEMPLATES["prompt_job_suitability_table"].format(
        job=pekerjaan,
        personality=tipe_kepribadian,
        cognitive=kognitif_utama_key,
        extracted_info=extracted_data
    )
    
    markdown_output = generate_ai_content(prompt, model=model_ai, task_name="Analisis Tabel Kecocokan")
    
    if "Error:" in markdown_output:
        print(f"   -- Gagal membuat tabel kecocokan. Respon: {markdown_output}")
        return []

    table_data = parse_markdown_table(markdown_output)
    print("   -- Analisis tabel kecocokan berhasil dibuat dan diparsing.")
    return table_data


def generate_ai_content(prompt, model="llama3.1:8b", task_name="AI Task"):
    """
    Fungsi generik untuk berinteraksi dengan model AI Ollama.
    """
    try:
        print(f"-> Mengirim request untuk '{task_name}' ke model {model}...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model, "prompt": prompt, "stream": False,
                "options": {
                    "temperature": 0.1, "top_p": 0.8, "num_predict": 2000,
                    "repeat_penalty": 1.2, "stop": ["Data referensi:", "Tugas:", "Instruksi:"]
                }
            },
            timeout=300
        )
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "").strip()
            if not generated_text:
                return f"Error: Model tidak menghasilkan response untuk {task_name}."
            
            # (Blok pembersih otomatis tetap ada)
            boilerplate_phrases = [
                "Berikut adalah ringkasan profil kandidat yang padat, lugas, dan profesional:",
                "Berikut adalah analisisnya:", "Tentu, berikut adalah analisisnya:",
                "Here is the analysis:", "Here's the analysis:",
                "Sebagai seorang konsultan SDM profesional,", "Sebagai seorang analis karir,"
            ]
            for phrase in boilerplate_phrases:
                if generated_text.lower().strip().startswith(phrase.lower()):
                    generated_text = generated_text[len(phrase):].lstrip(' :')
                    break
            
            print(f"   -- Berhasil meng-generate '{task_name}'.")
            return generated_text
        
        raise OllamaConnectionError(f"Error: HTTP {response.status_code} - {response.text}")

    except requests.exceptions.ConnectionError:
        # --- PERUBAHAN 2: Ganti 'return' dengan 'raise' ---
        raise OllamaConnectionError("Tidak bisa terhubung ke Ollama server. Pastikan 'ollama serve' sudah berjalan.")
    except Exception as e:
        raise OllamaConnectionError(f"Error saat generate {task_name}: {str(e)}")

# ==============================================================================
# BAGIAN 4: FUNGSI-FUNGSI UNTUK MENGGAMBAR PDF
# (Tidak ada perubahan di bagian ini)
# ==============================================================================
def draw_watermark(c, watermark_path):
    try:
        img = ImageReader(watermark_path)
        iw, ih = img.getSize()
        w_target = 130 * mm
        h_target = w_target * ih / iw
        x = (PAGE_WIDTH - w_target) / 2
        y = (PAGE_HEIGHT - h_target) / 2
        c.saveState()
        c.drawImage(img, x, y, width=w_target, height=h_target, mask='auto')
        c.restoreState()
    except Exception as e:
        print(f"⚠️ Watermark gagal dimuat: {e}")

def draw_header(c, logo_path="cia.png", is_cover=False):
    try:
        img = ImageReader(logo_path)
        iw, ih = img.getSize()
        w_target = 50 * mm
        h_target = w_target * ih / iw
        x = 20 * mm
        y = PAGE_HEIGHT - h_target - 10 * mm
        c.drawImage(img, x, y, width=w_target, height=h_target, mask='auto')
    except Exception as e:
        print(f"Logo gagal dimuat: {e}")

    c.setFont("Times-Bold", 14)
    c.drawRightString(PAGE_WIDTH - 25 * mm, PAGE_HEIGHT - 20 * mm, "CENTRAL IMPROVEMENT ACADEMY")
    c.setFont("Times-Roman", 12)
    c.drawRightString(PAGE_WIDTH - 25 * mm, PAGE_HEIGHT - 25 * mm, "Jl. Balikpapan No.27, RT.9/RW.6, Petojo Sel.,")
    c.drawRightString(PAGE_WIDTH - 25 * mm, PAGE_HEIGHT - 30 * mm, "Kecamatan Gambir, Jakarta Pusat")
    c.drawRightString(PAGE_WIDTH - 25 * mm, PAGE_HEIGHT - 35 * mm, "0811-3478-000")

    if not is_cover:
        c.setLineWidth(4)
        c.setStrokeColor(black)
        garis_y = PAGE_HEIGHT - 42 * mm
        c.line(25 * mm, garis_y, PAGE_WIDTH - 25 * mm, garis_y)


def draw_footer(c, page_num):
    c.setFont("Times-Roman", 12)
    c.drawRightString(PAGE_WIDTH - 10 * mm, 10 * mm, f"{page_num}")

def draw_centered_image(c, img_path, y_top, width_mm):
    try:
        image = ImageReader(img_path)
        iw, ih = image.getSize()
        width = width_mm * mm
        height = width * ih / iw
        x = (PAGE_WIDTH - width) / 2
        y = y_top - height
        c.drawImage(img_path, x, y, width=width, height=height, mask='auto')
        return y
    except Exception as e:
        print(f"Gambar '{img_path}' tidak ditemukan atau gagal dimuat: {e}")
        return y_top - 100


def halaman_1_cover(c, biodata, executive_summary_text, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    c.setFont("Times-Bold", 18)
    c.setFillColorRGB(0, 0.2, 0.6)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 150, "BRAIN WAVE PROFILING")
    c.setFillColor(black)

    c.setFont("Times-Roman", 12)
    y = PAGE_HEIGHT - 170
    for label, value in biodata.items():
        c.drawString(60, y, f"{label}")
        c.drawString(180, y, f": {value}")
        y -= 16

    y -= 15
    c.setFont("Times-Bold", 12)
    c.drawString(60, y, "EXECUTIVE SUMMARY")
    y -= 15
    c.setFont("Times-Roman", 12)


    style = ParagraphStyle(
        name="JustifySmall", fontName="Times-Roman", fontSize=12,
        leading=14, alignment=TA_JUSTIFY
    )
    summary_para = Paragraph(executive_summary_text, style)
    w, h = summary_para.wrap(PAGE_WIDTH - 2 * 60, 200)
    summary_para.drawOn(c, 60, y - h)

    draw_footer(c, page_num)
    c.showPage()

def halaman_2_kecocokan(c, table_data, page_num, personality_name, cognitive_name, job_name):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)
    
    y_start = PAGE_HEIGHT - 140
    c.setFont("Times-Bold", 12)
    c.drawString(60, y_start, f"ANALISIS KECOCOKAN UNTUK: {job_name.upper()}")
    
    cell_style = ParagraphStyle(
        "TableCell",
        fontSize=9,
        leading=11,
        wordWrap="CJK"
    )
    
    headers = [
        Paragraph("Kompetensi Utama", cell_style),
        Paragraph(f"{personality_name} (%)", cell_style),
        Paragraph(f"{cognitive_name} (%)", cell_style),
        Paragraph("Rata-rata Kesesuaian (%)", cell_style),
        Paragraph("Interpretasi", cell_style),
    ]
    
    data_for_table = [headers]
    for row in table_data:
        wrapped_row = [Paragraph(str(cell), cell_style) for cell in row]
        data_for_table.append(wrapped_row)
        
    # --- PERBAIKAN: Lebar kolom disesuaikan agar totalnya pas 18 cm ---
    col_widths = [5*cm, 3*cm, 3*cm, 3*cm, 3*cm]
    
    table = Table(data_for_table, colWidths=col_widths)
    
    table_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
    ])
    
    table.setStyle(table_style)
    
    w, h = table.wrapOn(c, PAGE_WIDTH - 120, y_start)
    table.drawOn(c, 60, y_start - h - 10)
    
    draw_footer(c, page_num)
    c.showPage()
    return page_num + 1

def halaman_3_behavior(c, behavior_traits_text, topoplot1, judul_topoplot1, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    y_start = PAGE_HEIGHT - 140
    c.setFont("Times-Bold", 12)
    c.drawString(60, y_start, "BEHAVIOR TRAITS PROFILE")

    style = ParagraphStyle(
        name="JustifySmall", fontName="Times-Roman", fontSize=12,
        leading=14, alignment=TA_JUSTIFY
    )

    y_topoplot = y_start - 40
    y_after_topoplot = draw_centered_image(c, topoplot1, y_topoplot, 180)

    judul_para = Paragraph(judul_topoplot1, style)
    max_text_width = PAGE_WIDTH - 2 * 60
    w_judul, h_judul = judul_para.wrap(max_text_width, PAGE_HEIGHT)
    y_judul = y_after_topoplot - h_judul - 10
    judul_para.drawOn(c, 60, y_judul)

    available_height = y_judul - 80
    lines = behavior_traits_text.split('\n') if '\n' in behavior_traits_text else behavior_traits_text.split('. ')
    current_text = ""
    text_parts = []
    
    for line in lines:
        temp_para = Paragraph(current_text + line + " ", style)
        _, h = temp_para.wrap(max_text_width, available_height)
        if h > available_height:
            text_parts.append(current_text.strip())
            current_text = line + " "
        else:
            current_text += line + " "
    if current_text:
        text_parts.append(current_text.strip())

    first_para = Paragraph(text_parts[0], style)
    w, h = first_para.wrap(max_text_width, available_height)
    first_para.drawOn(c, 60, y_judul - h - 20)
    draw_footer(c, page_num)
    c.showPage()
    
    current_page_number = page_num + 1
    for part in text_parts[1:]:
        draw_watermark(c, "cia_watermark.png")
        draw_header(c)
        para = Paragraph(part, style)
        w, h = para.wrap(max_text_width, PAGE_HEIGHT - 150)
        para.drawOn(c, 60, PAGE_HEIGHT - 150 - h)
        draw_footer(c, current_page_number)
        c.showPage()
        current_page_number += 1
    
    # --- PERBAIKAN: TAMBAHKAN BARIS RETURN DI BAWAH INI ---
    return current_page_number


def halaman_cognitive(c, cognitive_traits_text, topoplot2, judul_topoplot2, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    y_start = PAGE_HEIGHT - 140
    c.setFont("Times-Bold", 12)
    c.drawString(60, y_start, "COGNITIVE TRAITS")

    style = ParagraphStyle(
        name="JustifySmall", fontName="Times-Roman", fontSize=12,
        leading=14, alignment=TA_JUSTIFY
    )

    # Gambar topoplot
    y_topoplot = y_start - 40
    y_after_topoplot = draw_centered_image(c, topoplot2, y_topoplot, 180)

    # Judul topoplot
    judul_para = Paragraph(judul_topoplot2, style)
    max_text_width = PAGE_WIDTH - 2 * 60
    w_judul, h_judul = judul_para.wrap(max_text_width, PAGE_HEIGHT)
    y_judul = y_after_topoplot - h_judul - 5  # Kurangi gap dari -10 ke -5
    judul_para.drawOn(c, 60, y_judul)

    # Hitung ruang tersisa lebih akurat
    footer_height = 50  # Estimasi tinggi footer
    available_height = y_judul - footer_height - 10  # Margin bawah lebih kecil

    # Buat paragraph untuk seluruh teks
    full_para = Paragraph(cognitive_traits_text, style)
    
    # Cek apakah semua teks muat di halaman pertama
    w_full, h_full = full_para.wrap(max_text_width, available_height)
    
    if h_full <= available_height:
        # Semua teks muat di satu halaman
        text_y = y_judul - 10
        full_para.drawOn(c, 60, text_y - h_full)
        draw_footer(c, page_num)
        c.showPage()
        return page_num + 1
    
    # Jika tidak muat, bagi teks dengan lebih pintar
    sentences = cognitive_traits_text.replace('. ', '.|').split('|')
    
    current_page_text = ""
    remaining_text = ""
    split_found = False
    
    for sentence in sentences:
        test_text = current_page_text + sentence
        test_para = Paragraph(test_text, style)
        w_test, h_test = test_para.wrap(max_text_width, available_height)
        
        if h_test <= available_height and not split_found:
            current_page_text = test_text
        else:
            remaining_text += sentence
            split_found = True
    
    # Gambar teks halaman pertama
    if current_page_text:
        first_para = Paragraph(current_page_text, style)
        w_first, h_first = first_para.wrap(max_text_width, available_height)
        first_para.drawOn(c, 60, y_judul - 10 - h_first)
    
    draw_footer(c, page_num)
    c.showPage()
    
    # Halaman kedua jika ada sisa teks
    if remaining_text:
        draw_watermark(c, "cia_watermark.png")
        draw_header(c)
        
        # Lebih banyak ruang di halaman kedua
        y_start_page2 = PAGE_HEIGHT - 140
        available_height_page2 = y_start_page2 - footer_height - 20
        
        remaining_para = Paragraph(remaining_text, style)
        w_remaining, h_remaining = remaining_para.wrap(max_text_width, available_height_page2)
        remaining_para.drawOn(c, 60, y_start_page2 - h_remaining)
        
        draw_footer(c, page_num + 1)
        c.showPage()
        return page_num + 2
    
    return page_num + 1

def halaman_5(c, cognitive_traits_text_2,  page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    # Judul
    y_start = PAGE_HEIGHT - 110

    # Text Summary
    style = ParagraphStyle(
        name="JustifySmall",
        fontName="Times-Roman",
        fontSize=12,
        leading=14,
        alignment=TA_JUSTIFY,
    )
    summary_para = Paragraph(cognitive_traits_text_2, style)
    max_text_width = PAGE_WIDTH - 2 * 60  # margin kiri-kanan
    w, h = summary_para.wrap(max_text_width, PAGE_HEIGHT)
    
    y_text = y_start - 20  # padding bawah judul
    summary_para.drawOn(c, 60, y_text - h)

   

    draw_footer(c, page_num)
    c.showPage()

def halaman_person_fit_job(c, person_fit_job_text, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    y_pos = PAGE_HEIGHT - 140
    c.setFont("Times-Bold", 12)
    c.drawString(60, y_pos, "PERSON TO FIT BIDANG KERJA/USAHA")
    
    y_pos -= 15

    style = ParagraphStyle(
        name="JobFitStyle", fontName="Times-Roman", fontSize=12,
        leading=16, alignment=TA_JUSTIFY, spaceAfter=6
    )

    p = Paragraph(person_fit_job_text, style)

    margin_horizontal = 60
    text_width = PAGE_WIDTH - (2 * margin_horizontal)
    
    w, h = p.wrapOn(c, text_width, y_pos)
    p.drawOn(c, margin_horizontal, y_pos - h)

    draw_footer(c, page_num)
    c.showPage()
    
    # --- PERBAIKAN: TAMBAHKAN BARIS RETURN DI BAWAH INI ---
    return page_num + 1

def format_underline_links(text):
    return re.sub(
        r"(https?://[^\s\n]+)",
        r"<u><font color='#3366cc'>\1</font></u>",
        text
    )

def halaman_referensi(c, referensi_text_1, page_num):
    y_position = PAGE_HEIGHT - 150
    left_margin, right_margin, line_spacing = 60, 60, 5

    style = ParagraphStyle(
        name="JustifySmall", fontName="Times-Roman", fontSize=11.5,
        leading=14, alignment=TA_JUSTIFY, leftIndent=20,
        firstLineIndent=-20, spaceAfter=8, underlineWidth=0.4,
        underlineOffset= -2.5    
    )

    referensi_text_1 = format_underline_links(referensi_text_1)

    draw_watermark(c, "cia_watermark.png")
    draw_header(c)
    c.setFont("Times-Bold", 12)
    c.drawCentredString(PAGE_WIDTH / 2, y_position, "Referensi")
    y_position -= 15

    referensi_list = referensi_text_1.strip().split("\n\n")
    max_width = PAGE_WIDTH - left_margin - right_margin
    current_page_number = page_num
    
    for ref in referensi_list:
        ref_paragraph = Paragraph(ref.replace("\n", " "), style)
        w, h = ref_paragraph.wrap(max_width, PAGE_HEIGHT)

        if y_position - h < 80:
            draw_footer(c, current_page_number)
            c.showPage()
            current_page_number += 1
            draw_watermark(c, "cia_watermark.png")
            draw_header(c)
            y_position = PAGE_HEIGHT - 140

        ref_paragraph.drawOn(c, left_margin, y_position - h)
        y_position -= h + line_spacing

    draw_footer(c, current_page_number)
    c.showPage()
    
    # --- PERBAIKAN: TAMBAHKAN BARIS RETURN DI BAWAH INI ---
    return current_page_number + 1

def halaman_disclaimer(c, disclaimer_text, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    c.setFont("Times-Bold", 12)
    c.setFillColor(black)
    c.drawString(20 * mm, PAGE_HEIGHT - 150, "Disclaimer")

    left_margin, right_margin, top_margin = 20 * mm, 20 * mm, PAGE_HEIGHT - 170
    text_width = PAGE_WIDTH - left_margin - right_margin
    
    style = ParagraphStyle(
        name='Justified', fontName='Times-Roman', fontSize=10,
        leading=15, alignment=TA_JUSTIFY, underlineWidth=0.4,
        underlineOffset= -2.5    
    )
    
    text_for_paragraph = disclaimer_text.replace('\n', ' ').replace('  ', ' ')
    p = Paragraph(text_for_paragraph, style)
    w, h = p.wrapOn(c, text_width, PAGE_HEIGHT)
    p.drawOn(c, left_margin, top_margin - h)

    draw_footer(c, page_num)
    c.showPage()

    # --- PERBAIKAN: TAMBAHKAN BARIS RETURN DI BAWAH INI ---
    return page_num + 1

# ==============================================================================
# BAGIAN 5: FUNGSI UTAMA GENERATOR LAPORAN
# ==============================================================================
def generate_full_report(tipe_kepribadian, kognitif_utama_key, pekerjaan, model_ai, nama_file_output, biodata_kandidat, topoplot_path_behaviour, topoplot_path_cognitive):
    """
    Fungsi utama untuk menggenerate laporan profiling lengkap dari awal hingga akhir.
    
    Args:
        tipe_kepribadian (str): Nama trait kepribadian utama (e.g., "Openness").
        kognitif_utama_key (str): Kunci untuk trait kognitif utama (e.g., "WCST (Logika)").
        pekerjaan (str): Nama pekerjaan yang dilamar (e.g., "Tax Accountant").
        model_ai (str): Nama model Ollama yang akan digunakan (e.g., "llama3.1:8b").
        nama_file_output (str): Path untuk menyimpan file PDF hasil.
        biodata_kandidat (dict): Dictionary berisi biodata kandidat.
    """
    print("Memulai proses pembuatan laporan...")

    # --------------------------------------------------------------------------
    # A: MEMUAT DATA REFERENSI DAN KONTEN STATIS
    # --------------------------------------------------------------------------
    try:
        with open("bank_data.txt", "r", encoding="utf-8") as f:
            bank_data = f.read()
        print("Data referensi (bank_data.txt) berhasil dimuat.")
    except FileNotFoundError:
        print("Error: file 'bank_data.txt' tidak ditemukan! Proses dihentikan.")
        return

    # Muat konten statis berdasarkan input fungsi
    behavior_traits_text = BEHAVIOR_TRAITS_BANK.get(tipe_kepribadian, "Teks untuk kepribadian ini belum tersedia.")
    cognitive_traits_text = COGNITIVE_TRAITS_BANK.get(kognitif_utama_key, "Teks untuk kognitif ini belum tersedia.")
    kognitif_utama_display_name = kognitif_utama_key
    
    # Konten statis lainnya
    nama_kandidat = biodata_kandidat.get('Nama', 'Kandidat') # Mengambil nama dari biodata
    judul_topoplot1 = f"<b>Gambar 1. Topografi respons {nama_kandidat} terhadap stimulus behavioral trait {tipe_kepribadian.lower()}</b>"
    nama_kognitif_inti = kognitif_utama_key.split('(')[0].strip()
    judul_topoplot2 = f"<b>Gambar 2. Brain topografi Brain Wave Analysis Power stimulus {nama_kognitif_inti.lower()}</b>"
    
    referensi_text_1 = (
        "Alloway, T. P., Gathercole, S. E., & Pickering, S. J. (2009). The cognitive and behavioral "
        "characteristics of children with low working memory. Child Development, 80(2), 606–621. "
        "https://doi.org/10.1111/j.1467-8624.2009.01282.x\n\n"

        "Baddeley, A. D. (2003). Working memory: Looking back and looking forward. Nature "
        "Reviews Neuroscience, 4(10), 829-839. https://doi.org/10.1038/nrn1201\n\n"

        "Basar, E., Güntekin, B., & Yener, G. (2001). Brain oscillations and the processing of memory. "
        "International Journal of Psychophysiology, 39(3), 207-215. "
        "https://doi.org/10.1016/S0167-8760(00)00128-3\n\n"

        "Chen, R., et al. (2019). Personality Prediction Using EEG Signals and Machine Learning "
        "Algorithms. Social Cognitive and Affective Neuroscience.\n\n"

        "Cowan, N. (2001). The magical number 4 in short-term memory: A reconsideration of mental "
        "storage capacity. Behavioral and Brain Sciences, 24(1), 87-114. "
        "https://doi.org/10.1017/S0140525X01003922\n\n"

        "Euverman, L. (2024). The Emotion of Neuroticism: How neuroticism affects the perception of "
        "negative emotional stimuli. Tilburg University. https://arno.uvt.nl/show.cgi?fid=178809\n\n"

        "Eysenck, H. J. (1967). The Biological Basis of Personality. Springfield, IL: Charles C. Thomas.\n\n"

        "Gao, D., et al. (2023). Big five personality trait analysis from random eeg signal using "
        "convolutional neural network. Neuropsychologia.\n\n"

        "Gathercole, S. E., & Alloway, T. P. (2008). Working memory and learning: A practical guide. Sage "
        "Publications.\n\n"

        "Geng, Y., et al. (2024). Agreeableness modulates mental state decoding: Electrophysiological "
        "evidence. Human Brain Mapping, 45(2), 123–135. "
        "https://pubmed.ncbi.nlm.nih.gov/38339901/PubMed+1PMC+1\n\n"

        "Gevins, A., & Smith, M. E. (2003). Neurophysiological measures of cognitive workload during "
        "human-computer interaction. Theoretical Issues in Ergonomics Science, 4(1), 113–131. "
        "https://doi.org/10.1080/14639220210159709\n\n"

        "Gosling, S. D., & John, O. P. (2003). The Development of Personality Traits in Adulthood. "
        "Psychological Bulletin. "
        "https://www.researchgate.net/publication/247529145_The_Development_of_Personality_Traits_in_Adulthood\n\n"

        "Haas, B. W., et al. (2015). Agreeableness and brain activity during emotion attribution decisions. "
        "Journal of Research in Personality, 57, 142–151. "
        "https://www.sciencedirect.com/science/article/abs/pii/S0092656615000148ScienceDirect\n\n"

        "Isom-Schmidtke, J., et al. (2004). Personality, affect and EEG: Predicting patterns of regional brain "
        "activity related to extraversion and neuroticism. Personality and Individual Differences, 36(4), "
        "717–732. https://www.iomcworld.org/open-access/the-assessment-of-frontal-eeg-asymmetry"
        "according-to-neuroticism-and-extraversion-dimensions-57706.htmlInternational Online Medical Council+1ResearchGate+1\n\n"

        "Jaeggi, S. M., Buschkuehl, M., Jonides, J., & Perrig, W. J. (2008). Improving fluid intelligence "
        "with training on working memory. Proceedings of the National Academy of Sciences, "
        "105(19), 6829-6833. https://doi.org/10.1073/pnas.0801268105\n\n"

        "Jain, A. (2018). Personality and Job Performance: A Relational Perspective. International Journal of "
        "Management. "
        "https://www.researchgate.net/publication/324485496_Personality_and_Job_Performance_A_Relational_Perspective"
        "Jawinski, P., et al. (2021). The Big Five Personality Traits and Brain Arousal in the Resting State. "
        "Psychophysiology, 58(1), e13722. https://pubmed.ncbi.nlm.nih.gov/34679337/\n\n"

        "Jensen, O., & Tesche, C. D. (2002). Frontal theta activity in humans increases with memory load in a "
        "working memory task. European Journal of Neuroscience, 15(8), 1395–1399. "
        "https://doi.org/10.1046/j.1460-9568.2002.01975.x\n\n"

        "Klimesch, W. (1996). Memory processes, brain oscillations and EEG synchronization. International "
        "Journal of Psychophysiology, 24(1-2), 61-100. https://doi.org/10.1016/0167-8760(96)00043-4\n\n"

        "Klimesch, W. (1999). EEG alpha and theta oscillations reflect cognitive and memory performance: A "
        "review analysis. Brain Research Reviews, 29(2-3), 169-195. "
        "https://doi.org/10.1016/S0165-0173(98)00056-4\n\n"

        "Knyazev, G. G., et al. (2005). Personality traits and its association with resting regional brain activity. "
        "International Journal of Psychophysiology, 55(2). https://pubmed.ncbi.nlm.nih.gov/16019096/\n\n"

        "Knyazev, G. G., et al. (2007). Personality, gender and brain oscillations. International Journal of "
        "Psychophysiology, 66(1), 45-51. https://pubmed.ncbi.nlm.nih.gov/17761331/\n\n"

        "Li, J., et al. (2021). Big five personality trait analysis from random eeg signal using convolutional "
        "neural network. IEEE Transactions on Affective Computing.\n\n"

        "Li, W., et al. (2017). Neuronal correlates of individual differences in the Big Five personality traits: "
        "Evidences from cortical morphology and functional homogeneity. Frontiers in Neuroscience, 11, 414. "
        "https://www.frontiersin.org/articles/10.3389/fnins.2017.00414/full\n\n"

        "Liu, H., et al. (2022). Design and implementation of an EEG-based recognition mechanism for the "
        "openness trait of the Big Five. Journal of Neuroscience Methods.\n\n"

        "Liu, X., et al. (2018). Connecting Openness and the Resting-State Brain Network: A Discover-Validate "
        "Approach. Frontiers in Neuroscience, 12, 762. "
        "https://www.frontiersin.org/articles/10.3389/fnins.2018.00762/full\n\n"

        "Mulert, C., et al. (2017). A serotonin transporter gene polymorphism and the effect of tryptophan "
        "depletion on EEG synchronization. Biological Psychiatry. "
        "https://pubmed.ncbi.nlm.nih.gov/28988534/\n\n"

        "Neubauer, A. C., & Fink, A. (2009). Intelligence and neural efficiency. Brain and Cognition, 70(3), "
        "277-284. https://doi.org/10.1016/j.bandc.2009.04.007\n\n"

        "Onton, J., Delorme, A., & Makeig, S. (2005). Frontal midline EEG dynamics during working memory. "
        "NeuroImage, 27(2), 341–356. https://doi.org/10.1016/j.neuroimage.2005.04.014\n\n"

        "O'Reilly, R. C., & Frank, M. J. (2006). Making working memory work: A computational model of "
        "cognitive control. Trends in Cognitive Sciences, 10(11), 502-508. "
        "https://doi.org/10.1016/j.tics.2006.10.004\n\n"

        "Pfurtscheller, G., & Neuper, C. (2001). Functional brain imaging based on ERD/ERS. "
        "Electroencephalography and Clinical Neurophysiology, 110(5), 184-188. "
        "https://doi.org/10.1016/S0013-4694(98)00057-5\n\n"

        "Rana, M., et al. (2021). Emotion Analysis for Personality Inference from EEG Signals. "
        "Journal of Cognitive Neuroscience.\n\n"

        "Roslan, N. S., Izhar, L. I., Faye, I., & Abdul Rahman, M. (2017). Review of EEG and ERP studies of "
        "extraversion personality for baseline and cognitive tasks. Personality and Individual Differences, "
        "119, 323–332. https://doi.org/10.1016/j.paid.2017.08.004\n\n"

        "Roslan, N. S., Izhar, L. I., Faye, I., Amin, H. U., Mohamad Saad, M. N., Sivapalan, S., Abdul Karim, S. A., "
        "& Abdul Rahman, M. (2019). Neural correlates of eye contact in face-to-face verbal interaction: "
        "An EEG-based study of the extraversion personality trait. PLoS."
        
        "Sargent, J., et al. (2021). Frontal midline theta and gamma activity supports task control and "
        "conscientiousness. Neuroscience & Biobehavioral Reviews, 124, 69–77. "
        "https://www.sciencedirect.com/science/article/abs/pii/S0306453020305395\n\n"

        "Salthouse, T. A. (1996). The processing-speed theory of adult age differences in cognition. "
        "Psychological Review, 103(3), 403-428. https://doi.org/10.1037/0033-295X.103.3.403\n\n"

        "Sun, Y., et al. (2020). EEG-Based Personality Prediction Using Fast Fourier Transform and "
        "DeepLSTM Model. Cognitive Science.\n\n"

        "Tang, Y. Y., Ma, Y., Wang, J., Fan, Y., Feng, S., Lu, Q., ... & Posner, M. I. (2007). Short-term "
        "meditation training improves attention and self-regulation. PNAS, 104(43), 17152–17156. "
        "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2276138/\n\n"

        "Thut, G., Pascual-Leone, A., & Kuhn, M. (2006). Studies of brain stimulation and cognitive "
        "enhancement. NeuroImage, 31(1), 206-212. https://doi.org/10.1016/j.neuroimage.2005.12.054\n\n"

        "Tran, Y., Craig, A., & McIsaac, P. (2001). Extraversion/Introversion and 8–13 Hz wave in "
        "frontal cortical regions. Personality and Individual Differences, 30(2), 205–215. "
        "https://doi.org/10.1016/S0191-8869(00)00027-1\n\n"

        "Verywell Mind. (2021). What Are Alpha Brain Waves? "
        "https://www.verywellmind.com/what-are-alpha-brain-waves-5113721\n\n"

        "Vogel, E. K., McCollough, A. W., & Machizawa, M. G. (2005). Neural measures of individual "
        "differences in working memory capacity. Cerebral Cortex, 15(6), 748-756. "
        "https://doi.org/10.1093/cercor/bhh185\n\n"

        "Wang, L., et al. (2020). Big Five Personality Traits Prediction Using Brain Signals. Brain and Cognition.\n\n"

        "Wang, Y., et al. (2020). Decoding personality trait measures from resting EEG: An exploratory report. "
        "Personality and Individual Differences, 163, 110054. "
        "https://pubmed.ncbi.nlm.nih.gov/32653745/\n\n"

        "Wang, Y., Wang, Y., & Li, X. (2025). Extraversion and the Brain: A Coordinate-Based Meta-Analysis of "
        "Functional Brain Imaging Studies on Positive Affect. Human Brain Mapping, 46(3), 789–802. "
        "https://doi.org/10.1002/hbm.25345\n\n"

        "Wei, L., et al. (2011). Personality traits and the amplitude of spontaneous low-frequency oscillations "
        "during resting state. Neuroscience Letters, 492(2), 109-113. "
        "https://www.sciencedirect.com/science/article/abs/pii/S0304394011001133\n\n"

        "Yuan, F., et al. (2022). Personality Assessment Based on Electroencephalography Signals during Hazard Recognition. "
        "Cognitive Neuroscience.\n\n"

        "Zhang, Y., et al. (2021). EEG-Based Personality Prediction Using Fast Fourier Transform and DeepLSTM Model. "
        "Neuroscience Letters.\n\n"

        "Zhang, W., Zhou, Y., Zhang, Y., & Zhan, X. (2024). Event-related potentials study on the effects of high neuroticism "
        "on senile false memory. PLoS ONE, 19(8), e0304646. https://doi.org/10.1371/journal.pone.0304646\n\n"

        "Zhu, X., et al. (2020). EEG responses to emotional videos can quantitatively predict big-five personality traits. "
        "Frontiers in Human Neuroscience."
    )
    disclaimer_text = (
        'Profiling ini <b>bukan merupakan tes psikologi</b> melainkan '
        '<b>deskripsi profile respon elektrofisiologis sistem syaraf terhadap stimulus behavioral traits dan cognitive traits</b> '
        'yang dihitung melalui brain power EEG Emotive system yaitu skor EEG brain power enggagement, excitemen dan interest. '
        'Profiling ini menggunakan sumber bukti validitas dari penelitian sebelumnya. EEG dapat digunakan secara efektif untuk '
        'memprediksi kepribadian dengan akurasi yang tinggi. Zhu et al. (2020) melaporkan prediksi EEG trait agreeableness '
        'dengan akurasi hingga 86%. <u><font color="#3366cc">Zhu et al., 2020</font></u>. '
        '<u><font color="#3366cc">Liu et al., 2022</font></u> menunjukkan bahwa model berbasis EEG dapat mencapai akurasi 92.2% '
        'dalam memprediksi trait openness <u><font color="#3366cc">Liu et al., 2022</font></u>. '
        '<u><font color="#3366cc">Rana et al., 2021</font></u> menemukan bahwa analisis emosi dari sinyal EEG memprediksi extraversion '
        'dengan akurasi 81.08% dan agreeableness dengan 86.11% <u><font color="#3366cc">Rana et al., 2021</font></u>. '
        '<u><font color="#3366cc">Zhang et al., 2021</font></u> menggunakan model DeepLSTM untuk memprediksi kepribadian dengan '
        'akurasi signifikan <u><font color="#3366cc">Zhang et al., 2021</font></u>. '
        '<u><font color="#3366cc">Wang et al., 2020</font></u> melaporkan bahwa fitur sinyal otak dapat memprediksi trait Big Five '
        'dengan akurasi tinggi <u><font color="#3366cc">Wang et al., 2020</font></u>. '
        '<u><font color="#3366cc">Chen et al., 2019</font></u> menunjukkan bahwa algoritma pembelajaran mesin yang diterapkan '
        'pada sinyal EEG dapat secara efektif memprediksi kepribadian <u><font color="#3366cc">Chen et al., 2019</font></u>. '
        '<u><font color="#3366cc">Li et al., 2021</font></u> melakukan analisis kepribadian menggunakan sinyal EEG acak dengan '
        'akurasi yang memuaskan <u><font color="#3366cc">Li et al., 2021</font></u>. '
        '<u><font color="#3366cc">Yuan et al., 2022</font></u> menggunakan sinyal EEG dalam penilaian kepribadian selama pengenalan '
        'bahaya <u><font color="#3366cc">Yuan et al., 2022</font></u>. '
        '<u><font color="#3366cc">Gao et al., 2023</font></u> dan <u><font color="#3366cc">Sun et al., 2020</font></u> juga menunjukkan '
        'hasil yang konsisten potensi EEG sebagai alat yang kuat dalam analisis psikologis.'
    )

    table_data = []
    overall_suitability_level = None # Variabel untuk menyimpan level hasil klasifikasi
    overall_average = None

    print("\n--- Memulai Analisis Pra-Laporan ---")
    if pekerjaan and pekerjaan.strip():
        print("1. Membuat tabel kecocokan untuk menentukan level kesesuaian...")
        table_data = generate_suitability_analysis(
            pekerjaan, tipe_kepribadian, kognitif_utama_key, model_ai, bank_data
        )

        # --- BLOK YANG DIPERBARUI: KONVERSI MARKDOWN KE HTML UNTUK TABEL ---
        if table_data:
            print("   -- Mengonversi format markdown (bold & newline) di kolom 'Kompetensi Utama' ke HTML...")
            for row in table_data:
                # Cek untuk memastikan baris tidak kosong
                if len(row) > 0:
                    # Ambil teks asli dari kolom kompetensi
                    kompetensi_md = row[0]
                    
                    # Langkah 1: Ganti newline (\n) dengan tag <br/>
                    kompetensi_html = kompetensi_md.replace('\n', '<br/>')
                    
                    # Langkah 2: Ganti format bold (**teks**) dengan tag <b>teks</b>
                    kompetensi_html = re.sub(r'\*\*(.*?)\*\*', r'\1', kompetensi_html)
                    
                    # Masukkan kembali teks yang sudah bersih ke dalam baris data
                    row[0] = kompetensi_html
            print("   -- Konversi HTML untuk kolom kompetensi selesai.")
        # --- AKHIR BLOK YANG DIPERBARUI ---

        if table_data:
            try:
                # Logika perhitungan rata-rata (tidak berubah)
                average_scores = [float(row[3].replace('%', '')) for row in table_data]
                if average_scores:
                    overall_average = sum(average_scores) / len(average_scores)
                    
                    if overall_average >= 75:
                        overall_suitability_level = "Sangat Sesuai" 
                    elif overall_average >= 50:
                        overall_suitability_level = "Sesuai dengan Catatan Pengembangan"
                    else:
                        overall_suitability_level = "Kurang Sesuai"
                    print(f"   -- Rata-rata skor tabel: {overall_average:.2f}%. Level ditentukan sebagai: '{overall_suitability_level}'")
                else:
                    print("   -- Peringatan: Tidak ditemukan skor rata-rata yang valid di dalam data tabel.")
            except (ValueError, IndexError) as e:
                print(f"   -- Gagal menghitung rata-rata dari tabel: {e}. Level kesesuaian akan ditentukan oleh AI.")
        else:
            print("   -- Gagal membuat data tabel. Level kesesuaian akan ditentukan oleh AI.")

    # Inisialisasi variabel untuk menampung hasil AI
    executive_summary_formatted = "Konten Executive Summary gagal digenerate."
    person_fit_job_formatted = "Konten Person-Job Fit gagal digenerate."
    
    print("\n--- Memulai Generasi Konten AI ---")

    # --------------------------------------------------------------------------
    # B: GENERASI EXECUTIVE SUMMARY (PROSES 3 LANGKAH)
    # --------------------------------------------------------------------------
    print("2. Memulai proses untuk Executive Summary Otomatis...")
    executive_summary_formatted = generate_executive_summary(
        pekerjaan=pekerjaan,
        tipe_kepribadian=tipe_kepribadian,
        kognitif_utama=kognitif_utama_key,
        model_ai=model_ai,
        bank_data_text=bank_data,
        determined_level_from_table=overall_suitability_level,
        average_score_from_table=overall_average  # <-- TAMBAHKAN ARGUMEN INI
    )
    if "Error:" not in executive_summary_formatted:
        print("   -- Executive Summary otomatis berhasil dibuat.")
    else:
        print(f"   -- Gagal membuat Executive Summary. Respon: {executive_summary_formatted}")
    
    # --------------------------------------------------------------------------
    # C: GENERASI PERSON-JOB FIT
    # --------------------------------------------------------------------------
    print("3. Menggenerate konten Person-Job Fit...")
    keywords_for_summary = [tipe_kepribadian, kognitif_utama_key]
    specific_context_es = extract_relevant_data(bank_data, keywords_for_summary)
    prompt_job_fit = PROMPT_TEMPLATES["person_job_fit_full"].format(
        tipe_kepribadian=tipe_kepribadian,
        kognitif_utama=kognitif_utama_display_name,
        specific_context=specific_context_es
    )
    raw_markdown_text = generate_ai_content(prompt_job_fit, model=model_ai, task_name="Person-Job Fit (Markdown)")

    if "Error:" not in raw_markdown_text:
        print("   -- Mengonversi format Markdown ke HTML untuk PDF...")
        html_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', raw_markdown_text)
        person_fit_job_formatted = html_text.replace('\n', '<br/>')
        print("   -- Format HTML untuk Person-Job Fit berhasil dibuat.")
    else:
        person_fit_job_formatted = raw_markdown_text
        print(f"   -- Gagal meng-generate konten Person-Job Fit. Respon: {person_fit_job_formatted}")


    # --------------------------------------------------------------------------
    # D: PEMBUATAN PDF
    # --------------------------------------------------------------------------
    print(f"\n--- Memulai Pembuatan PDF: {nama_file_output} ---")
    c = canvas.Canvas(nama_file_output, pagesize=A4)
    
    # Inisialisasi nomor halaman
    next_page_num = 1
    
    # Halaman 1: Cover & Executive Summary
    halaman_1_cover(c, biodata_kandidat, executive_summary_formatted, page_num=next_page_num)
    next_page_num += 1

    # --- BLOK KONDISIONAL UNTUK TABEL KECOCOKAN ---
    if pekerjaan and pekerjaan.strip():
        if table_data: # Cek lagi jika tabel berhasil dibuat
            # Halaman 2: Tabel Kecocokan
            next_page_num = halaman_2_kecocokan(
                c, table_data, page_num=next_page_num,
                personality_name=tipe_kepribadian,
                cognitive_name=kognitif_utama_display_name,
                job_name=pekerjaan
            )
        else:
            print("   -- Gagal membuat data untuk tabel kecocokan, halaman akan dilewati.")
            
    # Halaman Berikutnya: Behavior Traits
    next_page_num = halaman_3_behavior(c, behavior_traits_text, topoplot_path_behaviour, judul_topoplot1, page_num=next_page_num)
    
    # Halaman Berikutnya: Cognitive Traits
    next_page_num = halaman_cognitive(c, cognitive_traits_text, topoplot_path_cognitive, judul_topoplot2, page_num=next_page_num)

    # Halaman Berikutnya: Person-Job Fit
    next_page_num = halaman_person_fit_job(c, person_fit_job_formatted, page_num=next_page_num)
    
    # Halaman Berikutnya: Referensi
    next_page_num = halaman_referensi(c, referensi_text_1, page_num=next_page_num)
    
    # Halaman Terakhir: Disclaimer
    next_page_num = halaman_disclaimer(c, disclaimer_text, page_num=next_page_num)

    c.save()
    print(f"\nPDF '{nama_file_output}' berhasil dibuat!")

    return person_fit_job_formatted, overall_suitability_level

# ==============================================================================
# BAGIAN 6: EKSEKUSI SCRIPT (ENTRY POINT)
# ==============================================================================
if __name__ == "__main__":
    
    config_tipe_kepribadian = "Conscientiousness"
    config_kognitif_utama = "WCST (Logika)" 
    config_pekerjaan = "Web Developer"
    config_model_ai = "llama3.1:8b"
    config_nama_file = "laporan_profiling_lengkap.pdf"
    
    config_biodata = {
        "Nama": "Denny Setiyawan",
        "Jenis kelamin": "Laki Laki",
        "Usia": "47 Tahun",
        "Alamat": "-",
        "Keperluan Test": "Profiling dengan Brain Wave Analysis response",
        "Tanggal Test": "31 Januari 2024",
        "Tempat Test": "Hotel Transformer Center, Batu, Jawa Timur.",
        "Operator": "Ahmad Marzuki S.Kom"
    }
    
    # Panggil fungsi utama dengan KONFIGURASI LENGKAP
    generate_full_report(
        tipe_kepribadian=config_tipe_kepribadian,
        kognitif_utama_key=config_kognitif_utama,
        pekerjaan=config_pekerjaan,
        model_ai=config_model_ai,
        nama_file_output=config_nama_file,
        biodata_kandidat=config_biodata,
        topoplot_path_behaviour="topoplot1.png",
        topoplot_path_cognitive="topoplot2.png"
    )