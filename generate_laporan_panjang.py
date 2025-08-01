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
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY

# ==============================================================================
# BAGIAN 2: KONSTANTA GLOBAL
# ==============================================================================
PAGE_WIDTH, PAGE_HEIGHT = A4

# ==============================================================================
# BAGIAN 3: FUNGSI GENERASI KONTEN AI
# ==============================================================================

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
            for heading in all_headings:
                found_pos = full_text.find(heading, start_index + 1)
                if found_pos != -1:
                    end_index = min(end_index, found_pos)
            chunk = full_text[start_index:end_index].strip()
            extracted_chunks.append(chunk)
        except ValueError:
            print(f"Peringatan: Keyword '{keyword}' tidak ditemukan di bank_data.txt")
    return "\n\n".join(extracted_chunks)

def generate_ai_content(prompt, model="llama3.1:8b", task_name="AI Task"):
    """
    Fungsi generik untuk berinteraksi dengan model AI Ollama.
    Versi ini memiliki pembersih otomatis untuk menghapus kalimat pembuka yang tidak diinginkan.
    """
    try:
        print(f"-> Mengirim request untuk '{task_name}' ke model {model}...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
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

            # --- BLOK PEMBERSIH OTOMATIS ---
            # Daftar kalimat pembuka yang akan dideteksi dan dihapus
            boilerplate_phrases = [
                "Berikut adalah ringkasan profil kandidat yang padat, lugas, dan profesional:",
                "Berikut adalah analisisnya:",
                "Tentu, berikut adalah analisisnya:",
                "Here is the analysis:",
                "Here's the analysis:",
                "Sebagai seorang konsultan SDM profesional,",
                "Sebagai seorang analis karir,"
            ]
            
            # Periksa setiap frasa dan hapus jika ditemukan di awal jawaban
            for phrase in boilerplate_phrases:
                # Menggunakan lower() untuk perbandingan case-insensitive
                if generated_text.lower().strip().startswith(phrase.lower()):
                    # Hapus frasa tersebut dari awal teks
                    generated_text = generated_text[len(phrase):].lstrip(' :')
                    print(f"   -- Kalimat pembuka terdeteksi dan dibersihkan.")
                    break # Hentikan setelah menemukan satu kecocokan
            # --------------------------------

            print(f"   -- Berhasil meng-generate '{task_name}'.")
            return generated_text

        return f"Error: HTTP {response.status_code} - {response.text}"
    except requests.exceptions.ConnectionError:
        return "Error: Tidak bisa connect ke Ollama server. Pastikan 'ollama serve' sudah jalan."
    except Exception as e:
        return f"Error saat generate {task_name}: {str(e)}"

# ==============================================================================
# BAGIAN 4: FUNGSI-FUNGSI UNTUK MENGGAMBAR PDF
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

def halaman_2(c, behavior_traits_text, topoplot1, judul_topoplot1, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)
    y_start = PAGE_HEIGHT - 170
    c.setFont("Times-Bold", 12)
    c.drawString(60, y_start, "BEHAVIOR TRAITS PROFILE")

    style = ParagraphStyle(
        name="JustifySmall", fontName="Times-Roman", fontSize=12,
        leading=14, alignment=TA_JUSTIFY
    )
    summary_para = Paragraph(behavior_traits_text, style)
    max_text_width = PAGE_WIDTH - 2 * 60
    w, h = summary_para.wrap(max_text_width, PAGE_HEIGHT)
    y_text = y_start - 20
    summary_para.drawOn(c, 60, y_text - h)

    padding_after_text = 20
    y_topoplot1 = y_text - h - padding_after_text
    y = draw_centered_image(c, topoplot1, y_topoplot1, 180)

    judul_para = Paragraph(judul_topoplot1, style)
    w_judul, h_judul = judul_para.wrap(max_text_width, PAGE_HEIGHT)
    y_judul_topoplot1 = y - h_judul - 10
    judul_para.drawOn(c, 60, y_judul_topoplot1)

    draw_footer(c, page_num)
    c.showPage()

def halaman_3(c, behavior_traits_text_2, page_num):
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
    summary_para = Paragraph(behavior_traits_text_2, style)
    max_text_width = PAGE_WIDTH - 2 * 60  # margin kiri-kanan
    w, h = summary_para.wrap(max_text_width, PAGE_HEIGHT)
    
    y_text = y_start - 20  # padding bawah judul
    summary_para.drawOn(c, 60, y_text - h)

    draw_footer(c, page_num)
    c.showPage()

def halaman_4(c, cognitive_traits_text, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    # Judul
    y_start = PAGE_HEIGHT - 170
    c.setFont("Times-Bold", 12)
    c.drawString(60, y_start, "COGNITIVE TRAITS")
    
    # Text Summary
    style = ParagraphStyle(
        name="JustifySmall",
        fontName="Times-Roman",
        fontSize=12,
        leading=14,
        alignment=TA_JUSTIFY,
    )
    summary_para = Paragraph(cognitive_traits_text, style)
    max_text_width = PAGE_WIDTH - 2 * 60  # margin kiri-kanan
    w, h = summary_para.wrap(max_text_width, PAGE_HEIGHT)
    
    y_text = y_start - 20  # padding bawah judul
    summary_para.drawOn(c, 60, y_text - h)

    draw_footer(c, page_num)
    c.showPage()

def halaman_5(c, cognitive_traits_text_2, topoplot2, judul_topoplot2, page_num):
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

    # --- Gambar Topoplot 2 di bawah teks ---
    padding_after_text = 20  # padding setelah paragraf
    y_topoplot2 = y_text - h - padding_after_text
    y = draw_centered_image(c, topoplot2, y_topoplot2, 180)
    
    judul_topoplot2 = Paragraph(judul_topoplot2,style)
    max_text_width = PAGE_WIDTH - 2 * 60  # margin kiri-kanan
    w, h = judul_topoplot2.wrap(max_text_width, PAGE_HEIGHT)
    y_judul_topoplot2 = y - h - 10  # padding atas
    judul_topoplot2.drawOn(c, 60, y_judul_topoplot2)

    draw_footer(c, page_num)
    c.showPage()

def halaman_person_fit_job(c, person_fit_job_text, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    # Judul
    y_pos = PAGE_HEIGHT - 170
    c.setFont("Times-Bold", 12)
    c.drawString(60, y_pos, "PERSON TO FIT BIDANG KERJA/USAHA")
    
    # Beri sedikit jarak setelah judul
    y_pos -= 30

    # Definisikan style untuk paragraf yang akan merender HTML
    style = ParagraphStyle(
        name="JobFitStyle",
        fontName="Times-Roman",
        fontSize=12,
        leading=16,  # Beri jarak antar baris yang cukup
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )

    # Buat objek Paragraph dari teks yang dihasilkan AI
    # Objek ini akan menginterpretasikan tag <b> dan <br/>
    p = Paragraph(person_fit_job_text, style)

    # Tentukan lebar area teks dan gambar ke kanvas
    margin_horizontal = 60
    text_width = PAGE_WIDTH - (2 * margin_horizontal)
    
    # Hitung tinggi yang dibutuhkan dan gambar paragrafnya
    w, h = p.wrapOn(c, text_width, y_pos)
    p.drawOn(c, margin_horizontal, y_pos - h)

    draw_footer(c, page_num)
    c.showPage()

from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_JUSTIFY
import re
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY

def format_underline_links(text):
    return re.sub(
        r"(https?://[^\s\n]+)",
        r"<u><font color='#3366cc'>\1</font></u>",
        text
    )

def halaman_8(c, referensi_text_1, page_num):
    y_position = PAGE_HEIGHT - 150  # awal di bawah judul
    left_margin = 60
    right_margin = 60
    line_spacing = 5

    # Style hanging indent + support link underline
    style = ParagraphStyle(
        name="JustifySmall",
        fontName="Times-Roman",
        fontSize=11.5,
        leading=14,
        alignment=TA_JUSTIFY,
        leftIndent=20,
        firstLineIndent=-20,
        spaceAfter=8,
        underlineWidth=0.4,
        underlineOffset= -2.5    
    )

    # Format semua link dalam referensi jadi underline biru
    referensi_text_1 = format_underline_links(referensi_text_1)

    # Gambar header dan judul
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)
    c.setFont("Times-Bold", 12)
    c.drawCentredString(PAGE_WIDTH / 2, y_position, "Referensi")
    y_position -= 15  # Jarak dari judul ke teks

    # Pecah berdasarkan double newline antar referensi
    referensi_list = referensi_text_1.strip().split("\n\n")
    max_width = PAGE_WIDTH - left_margin - right_margin

    for ref in referensi_list:
        ref_paragraph = Paragraph(ref.replace("\n", " "), style)
        w, h = ref_paragraph.wrap(max_width, PAGE_HEIGHT)

        # Jika tidak muat di halaman sekarang, pindah halaman
        if y_position - h < 80:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1

            # --- RESET HEADER HALAMAN BARU ---
            draw_watermark(c, "cia_watermark.png")
            draw_header(c)
            y_position = PAGE_HEIGHT - 140

        # Gambar referensi
        ref_paragraph.drawOn(c, left_margin, y_position - h)
        y_position -= h + line_spacing

    # Footer terakhir
    draw_footer(c, page_num)
    c.showPage()

        
def halaman_11(c, disclaimer_text, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    c.setFont("Times-Bold", 12)
    c.setFillColor(black)
    c.drawString(20 * mm, PAGE_HEIGHT - 150, "Disclaimer")

    # Margin untuk area teks
    left_margin = 20 * mm
    right_margin = 20 * mm
    top_margin = PAGE_HEIGHT - 170 # Posisi Y untuk bagian atas paragraf
    
    # Lebar area yang tersedia untuk teks
    text_width = PAGE_WIDTH - left_margin - right_margin
    
    # Buat style untuk paragraf: rata kiri-kanan (justify)
    style = ParagraphStyle(
        name='Justified',
        fontName='Times-Roman',
        fontSize=10,
        leading=15,  # Jarak antar baris
        alignment=TA_JUSTIFY,
        underlineColor=None,
        underlineWidth=0.4,
        underlineOffset= -2.5    
    )
    
    # Ganti spasi biasa dengan spasi yang lebih 'fleksibel' untuk justifikasi yang lebih baik
    # dan ubah kalimat-kalimat terpisah menjadi satu blok teks
    text_for_paragraph = disclaimer_text.replace('\n', ' ').replace('  ', ' ')
    
    # Buat objek Paragraf
    p = Paragraph(text_for_paragraph, style)
    
    # Hitung tinggi yang dibutuhkan oleh paragraf dan gambar ke kanvas
    w, h = p.wrapOn(c, text_width, PAGE_HEIGHT) # wrapOn untuk kalkulasi
    p.drawOn(c, left_margin, top_margin - h) # drawOn untuk menggambar

    c.setFont("Times-Bold", 10)
    c.setFillColorRGB(0.6, 0.6, 0.6)

    draw_footer(c, page_num)
    c.showPage()

# ==============================================================================
# BAGIAN 5: EKSEKUSI UTAMA
# ==============================================================================
if __name__ == "__main__":

    # --------------------------------------------------------------------------
    # A: KONFIGURASI
    # --------------------------------------------------------------------------
    TIPE_KEPRIBADIAN = "Agreeableness"
    KOGNITIF_UTAMA_KEY = "Digit Span (Short Term Memory)" 
    PEKERJAAN = "Tax Accountant"
    MODEL_AI = "llama3.1:8b"
    NAMA_FILE_OUTPUT = "laporan_profiling_lengkap.pdf"
    
    kognitif_utama_display_name = KOGNITIF_UTAMA_KEY

    # --------------------------------------------------------------------------
    # B: TEMPLATE PROMPT AI
    # --------------------------------------------------------------------------

    # B: TEMPLATE PROMPT AI (Versi Final dengan Contoh/Few-Shot)
    PROMPT_TEMPLATES = {
        # "executive_summary_narrative": """
        # Anda adalah seorang ahli psikologi industri dan organisasi (PIO). Tugas Anda adalah meniru GAYA ANALISIS dan FORMAT OUTPUT dari contoh di bawah untuk menghasilkan sebuah executive summary.

        # ======================================
        # CONTOH KASUS & OUTPUT IDEAL (TIRU GAYA INI)
        # ======================================
        # --- CONTOH INPUT DATA ---
        # - Tipe Kepribadian Utama: Conscientiousness (Kekuatan: Teliti, teratur. Kelemahan: Kaku)
        # - Kekuatan Kognitif Utama: Logika WCST (Kekuatan: Penalaran abstrak)
        # - Posisi yang Dilamar: Software Tester

        # --- CONTOH HASIL AKHIR PARAGRAF (INI ADALAH FORMAT OUTPUT YANG SAYA INGINKAN) ---
        # Individu ini dinilai **Cocok** untuk posisi Software Tester. Kekuatan utamanya yang didorong oleh sifat **Conscientiousness** yang tinggi membuatnya memiliki **ketelitian dan keteraturan** yang sangat selaras dengan tuntutan inti untuk menemukan anomali perangkat lunak. Kemampuan **logika abstraknya** juga mendukung dalam merancang skenario pengujian yang efektif. Meskipun demikian, terdapat area pengembangan minor pada aspek **kecenderungan untuk bersikap kaku**, yang perlu diperhatikan saat menghadapi perubahan prioritas pengujian yang dinamis. Dengan pembinaan untuk meningkatkan fleksibilitas, individu ini berpotensi menjadi Software Tester yang andal.
        
        # ======================================
        # TUGAS AKHIR & ATURAN MUTLAK
        # ======================================
        
        # **TUGAS ANDA:**
        # SEKARANG, ANALISIS DATA DI BAWAH INI. TIRU GAYA DAN FORMAT DARI CONTOH DI ATAS UNTUK MENGHASILKAN **SATU PARAGRAF** EXECUTIVE SUMMARY FINAL.

        # **DATA UNTUK DIANALISIS:**
        # - Tipe Kepribadian Utama: {tipe_kepribadian}
        # - Kekuatan Kognitif Utama: {kognitif_utama}
        # - Posisi yang Dilamar: {pekerjaan}
        # - Konteks Tambahan dari Tes: {specific_context}

        # **ATURAN PALING UTAMA:**
        # OUTPUT ANDA **HANYA BOLEH** TERDIRI DARI SATU PARAGRAF ANALISIS FINAL. JANGAN MENULIS APAPUN SELAIN PARAGRAF TERSEBUT.
        # """,
        # PROMPT BARU - LANGKAH 1
        "prompt_step1_deep_analysis_and_score": """
        Anda adalah seorang ahli psikologi industri dan organisasi (PIO) senior.
        
        TUGAS: Lakukan analisis MENTAH yang sangat detail dalam format poin-poin. JANGAN MENULIS PARAGRAF. Di akhir, berikan penilaian skor mentah dari 1 (sangat tidak cocok) hingga 10 (sangat cocok) beserta justifikasinya.
        
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

        # LANGKAH 2: PENENTUAN LABEL KECOCOKAN
        "prompt_step2_determine_level": """
        Anda adalah seorang quality control analyst.
        
        TUGAS: Berdasarkan analisis dan skor di bawah, pilih SATU label yang paling sesuai dari tiga opsi berikut: "Sangat Cocok", "Cocok dengan Catatan Pengembangan", "Kurang Cocok".
        
        PANDUAN PEMILIHAN LABEL:
        - Skor 8-10: Pilih "Sangat Cocok"
        - Skor 5-7: Pilih "Cocok dengan Catatan Pengembangan"
        - Skor 1-4: Pilih "Kurang Cocok"
        
        ANALISIS UNTUK DIEVALUASI:
        ---
        {deep_analysis_and_score}
        ---
        
        ATURAN: Output Anda HANYA berupa salah satu dari tiga label tersebut. Jangan menulis apa pun lagi.
        """,

        # LANGKAH 3: PENULISAN NARASI FINAL
        "prompt_step3_write_narrative": """
        Anda adalah seorang penulis laporan psikologi industri senior yang ahli dalam menyusun analisis yang mendalam dan actionable.

        TUGAS: Tulis **DUA PARAGRAF** executive summary yang komprehensif dan profesional berdasarkan analisis mentah dan label kecocokan yang sudah ditentukan.

        ======================================
        DATA UNTUK DITULIS:
        - Label Kecocokan yang Telah Ditentukan: "{determined_level}"
        - Analisis Mentah Lengkap:
        ---
        {deep_analysis_and_score}
        ---
        ======================================

        INSTRUKSI PENULISAN WAJIB:

        **Paragraf 1: FOKUS PADA DIAGNOSIS KECOCOKAN**
        1.  Awali dengan menyatakan level kecocokan yang telah ditentukan (Contoh: "Berdasarkan analisis profil, individu ini dinilai **{determined_level}** untuk posisi...").
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

        "person_job_fit_full": """
        Anda adalah seorang analis karir ahli. Tugas Anda adalah membuat analisis rekomendasi bidang kerja yang cocok berdasarkan profil kandidat dengan format yang spesifik dan terstruktur.

        ==============================
        **TEMPLATE FORMAT YANG HARUS DIIKUTI PERSIS:**
        ==============================
        
        Individu dengan kepribadian [KEPRIBADIAN] dan kemampuan [KOGNITIF] akan optimal dalam pekerjaan yang membutuhkan [sebutkan karakteristik kerja yang spesifik sesuai profil]. Berikut adalah beberapa bidang kerja yang sesuai:
        
        **[Nama Kategori Bidang 1]**
        [Job Title 1], [Job Title 2], [Job Title 3]. [Penjelasan 2-3 kalimat mengapa bidang ini cocok, bagaimana kepribadian dan kognitif dimanfaatkan dalam pekerjaan tersebut, serta contoh tugas spesifik].
        
        **[Nama Kategori Bidang 2]**  
        [Job Title 1], [Job Title 2]. [Penjelasan 2-3 kalimat mengapa bidang ini cocok, bagaimana kepribadian dan kognitif dimanfaatkan dalam pekerjaan tersebut, serta contoh tugas spesifik].
        
        **[Nama Kategori Bidang 3]**
        [Job Title 1], [Job Title 2]. [Penjelasan 2-3 kalimat mengapa bidang ini cocok, bagaimana kepribadian dan kognitif dimanfaatkan dalam pekerjaan tersebut, serta contoh tugas spesifik].
        
        **[Nama Kategori Bidang 4]**
        [Job Title 1], [Job Title 2]. [Penjelasan 2-3 kalimat mengapa bidang ini cocok, bagaimana kepribadian dan kognitif dimanfaatkan dalam pekerjaan tersebut, serta contoh tugas spesifik].
        
        **[Nama Kategori Bidang 5]**
        [Job Title 1], [Job Title 2]. [Penjelasan 2-3 kalimat mengapa bidang ini cocok, bagaimana kepribadian dan kognitif dimanfaatkan dalam pekerjaan tersebut, serta contoh tugas spesifik].

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
        - Langsung lanjut dengan penjelasan dalam 1 paragraf (2-3 kalimat)
        4. **BERIKAN 5 KATEGORI** bidang kerja yang berbeda dan spesifik
        5. **PENJELASAN SETIAP KATEGORI HARUS**:
        - Menjelaskan mengapa cocok dengan profil
        - Menyebutkan bagaimana kepribadian digunakan
        - Menyebutkan bagaimana kemampuan kognitif dimanfaatkan
        - Memberikan contoh tugas atau situasi kerja spesifik
        6. **BAHASA**: Gunakan Bahasa Indonesia yang profesional dan formal
        7. **JANGAN** gunakan bullet points, numbering, atau tag HTML
        8. **KONSISTENSI**: Ikuti format template tanpa variasi apapun
        9. **SPESIFIK**: Semua rekomendasi harus logis dan relevan dengan kombinasi kepribadian + kognitif yang diberikan
     """
    }
    # --------------------------------------------------------------------------
    # C: KONTEN STATIS UNTUK LAPORAN
    # --------------------------------------------------------------------------
    biodata = {
        "Nama": "Denny Setiyawan",
        "Jenis kelamin": "Laki Laki",
        "Usia": "47 Tahun",
        "Alamat": "-",
        "Keperluan Test": "Profiling dengan Brain Wave Analysis response",
        "Tanggal Test": "31 Januari 2024",
        "Tempat Test": "Hotel Transformer Center, Batu, Jawa Timur.",
        "Operator": "Ahmad Marzuki S.Kom"
    }
    
    # Teks ini tetap statis sesuai file asli
    behavior_traits_text = (
        "Hasil analisis EEG menunjukkan bahwa individu dengan tingkat Extraversion yang tinggi "
        "cenderung memiliki aktivitas otak yang khas. Penelitian oleh Tran et al. (2001) menemukan "
        "bahwa individu ekstrovert menunjukkan amplitudo gelombang alfa (8–13 Hz) yang lebih tinggi "
        "di area frontal korteks dibandingkan dengan individu introvert. Temuan ini menunjukkan "
        "bahwa ekstrovert memiliki tingkat arousal kortikal yang lebih rendah, yang konsisten dengan "
        "teori arousal oleh Eysenck (1967) yang menyatakan bahwa ekstrovert memiliki tingkat arousal "
        "kortikal yang lebih rendah dan oleh karena itu mencari stimulasi eksternal untuk mencapai "
        "tingkat arousal optimal."
        
        "<br/><br/>"

        "Selain itu, studi oleh Roslan et al. (2019) menunjukkan bahwa selama interaksi tatap muka, "
        "individu dengan tingkat Extraversion yang tinggi menunjukkan koherensi alfa yang lebih besar "
        "di wilayah oksipital, yang berkaitan dengan pemrosesan informasi visual dan perhatian "
        "terhadap isyarat sosial seperti kontak mata. Hal ini menunjukkan bahwa ekstrovert lebih "
        "responsif terhadap isyarat sosial selama interaksi interpersonal."

        "<br/><br/>"

        "Lebih lanjut, meta-analisis oleh Wang et al. (2025) mengidentifikasi bahwa Extraversion "
        "berkorelasi positif dengan aktivasi di gyrus frontal inferior kanan dan insula selama "
        "pemrosesan afek positif, serta aktivasi di gyrus angular kanan dan gyrus precentral kiri. "
        "Temuan ini menunjukkan bahwa ekstrovert memiliki respons neural yang lebih kuat terhadap "
        "rangsangan emosional positif, yang mendukung kecenderungan mereka untuk mencari "
        "pengalaman yang menyenangkan dan interaksi sosial."
    )
    
    judul_topoplot1 = "<b>Gambar 1. Topografi response Yudanta Adhipramana terhadap stimulus behavioral trait extraversion</b>"
    
    behavior_traits_text_2 = (
        "Individu dengan tingkat Exraversion yang tinggi dikenal karena sifat sosial, energik, dan " 
        "optimis mereka. Mereka cenderung menikmati interaksi sosial, memiliki jaringan sosial yang "
        "luas, dan merasa nyaman dalam situasi yang melibatkan banyak orang. Namun, trait ini juga "
        "dapat memiliki kelemahan, seperti kecenderungan untuk mencari stimulasi berlebihan yang "
        "dapat mengarah pada perilaku impulsif atau kurangnya perhatian terhadap detail. Dalam "
        "konteks profesional, ekstrovert mungkin unggul dalam peran yang memerlukan interaksi sosial "
        "yang intensif, seperti penjualan, hubungan masyarakat, atau kepemimpinan tim. "
    
        "<br/><br/>"
        
        "Trait Extraversion dapat dikembangkan melalui pelatihan yang mendorong keterlibatan sosial "
        "dan peningkatan keterampilan komunikasi. Program pengembangan diri yang fokus pada "
        "peningkatan kepercayaan diri dalam situasi sosial, serta pelatihan dalam keterampilan " 
        "interpersonal, dapat membantu individu menjadi lebih ekstrovert. Selain itu, pengalaman " 
        "positif dalam interaksi sosial dapat memperkuat kecenderungan ekstrovert dan meningkatkan " 
        "kesejahteraan psikologis secara keseluruhan. "
    )

    cognitive_traits_text = (
        "Hasil tes EEG pada stimulus yang menguji memori jangka pendek menunjukkan pola respons "
        "elektrofisiologis yang lebih kuat pada gelombang theta dan alpha, yang berhubungan dengan "
        "pengolahan informasi jangka pendek. Aktivitas yang lebih dominan terlihat pada kanal-kanal "
        "posterior, seperti P3 dan O1, yang terletak di area temporal dan oksipital otak, yang terkait "
        "dengan pemrosesan visual dan pengingatan informasi dalam waktu singkat. Penelitian "
        "menunjukkan bahwa peningkatan aktivitas gelombang theta di area ini berhubungan dengan "
        "pengolahan dan penyimpanan informasi dalam memori jangka pendek (Klimesch, 1996; Basar "
        "et al., 2001). Aktivitas ini dapat terjadi saat individu diminta untuk mengingat serangkaian "
        "angka atau kata dalam jangka waktu yang terbatas, yang mengindikasikan keterlibatan intens "
        "dalam memori jangka pendek."
        
        "<br/><br/>"

        "Keunggulan utama dari individu dengan kemampuan memori jangka pendek yang tinggi "
        "adalah kemampuan untuk mengingat dan memproses informasi dalam waktu yang sangat "
        "singkat, yang sangat penting dalam berbagai situasi yang membutuhkan pengambilan "
        "keputusan cepat. Penelitian oleh Cowan (2001) menunjukkan bahwa individu dengan kapasitas "
        "memori jangka pendek yang lebih besar dapat lebih efisien dalam menyelesaikan tugas-tugas "
        "yang membutuhkan pengingatan informasi untuk waktu yang terbatas, seperti dalam "
        "percakapan cepat atau saat mengambil keputusan dalam lingkungan yang penuh informasi. "
        "Mereka cenderung memiliki kemampuan lebih untuk mengingat instruksi, angka, atau urutan "
        "informasi dengan cepat, yang memberikan keunggulan dalam situasi kerja atau pembelajaran "
        "yang melibatkan memori aktif. "
        "<br/><br/>"

        "Namun, kelemahan utama individu dengan memori jangka pendek yang tinggi adalah "
        "keterbatasan dalam mengingat informasi dalam jangka waktu yang lebih lama. Penelitian "
        "menunjukkan bahwa meskipun mereka mampu menyimpan dan mengingat informasi dalam "
        "waktu singkat, mereka mungkin mengalami kesulitan dalam mempertahankan informasi "
        "tersebut dalam jangka panjang, yang berpotensi menghambat kemampuan mereka dalam "
        "situasi yang membutuhkan pengingatan informasi secara permanen (Baddeley, 2003). Hal ini "
        "dapat mempengaruhi kemampuan mereka untuk mengingat informasi yang telah dipelajari "
        "dalam konteks jangka panjang, yang menjadi penting dalam pembelajaran atau pengelolaan "
        "informasi yang lebih rumit dan memerlukan integrasi informasi. "
        "<br/><br/>"
        
        "Dalam konteks pengembangan, kemampuan memori jangka pendek dapat ditingkatkan melalui "
        "latihan yang menstimulasi proses penyimpanan dan pengambilan informasi dalam jangka "
        "waktu singkat. Berbagai teknik pelatihan, seperti latihan ingatan berbasis urutan atau "
        "permainan otak yang melibatkan peningkatan kecepatan pengingatan, dapat membantu "
        "memperkuat kemampuan memori jangka pendek. Penelitian menunjukkan bahwa pelatihan "
        "yang melibatkan pengulangan informasi dalam waktu singkat dapat meningkatkan kapasitas "
        "memori jangka pendek (Salthouse, 1996; Jaeggi et al., 2008). Selain itu, latihan yang "
        "melibatkan pengolahan informasi dalam konteks yang lebih variatif juga dapat membantu "
        "mempercepat pemrosesan informasi dalam memori jangka pendek, sehingga individu menjadi "
        "lebih efisien dalam menyelesaikan tugas-tugas yang membutuhkan ketahanan memori."
    )
    
    cognitive_traits_text_2 = (
        "Hasil penelitian EEG menunjukkan bahwa kanal-kanal yang terlibat dalam memori jangka "
        "pendek, seperti P3 dan O1, berfungsi dalam konteks pengolahan informasi visual dan verbal "
        "dalam waktu yang singkat. Peningkatan aktivitas gelombang theta dan alpha di area posterior "
        "menunjukkan bahwa otak sedang bekerja untuk memanipulasi informasi yang baru saja "
        "diterima dan menyimpannya dalam memori jangka pendek (Vogel et al., 2005). Hal ini sangat "
        "penting dalam memahami bagaimana individu dengan memori jangka pendek yang kuat dapat "
        "lebih efektif dalam pengambilan keputusan cepat dan dalam situasi yang melibatkan "
        "pengingatan informasi dengan durasi singkat."
    )
    
    judul_topoplot2 = "<b>Gambar 2.Brain topografi Brain Wave Analysis Power stimulus digit span</b>"
    
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

    # --------------------------------------------------------------------------
    # D: PROSES UTAMA - GENERASI KONTEN DAN PEMBUATAN PDF
    # --------------------------------------------------------------------------
    print("Memulai proses pembuatan laporan...")

    try:
        with open("bank_data.txt", "r", encoding="utf-8") as f:
            bank_data = f.read()
        print("Data referensi (bank_data.txt) berhasil dimuat.")
    except FileNotFoundError:
        print("Error: file 'bank_data.txt' tidak ditemukan! Proses dihentikan.")
        exit()

    # Inisialisasi variabel untuk menampung hasil AI
    executive_summary_formatted = "Konten Executive Summary gagal digenerate."
    person_fit_job_formatted = "Konten Person-Job Fit gagal digenerate."

    print("\n--- Memulai Generasi Konten AI ---")

    # === LANGKAH 1: GENERATE EXECUTIVE SUMMARY (METODE 3 LANGKAH OTOMATIS) ===
    print("1. Memulai proses 3 langkah untuk Executive Summary Otomatis...")

    # -- Langkah 1: Analisis Mendalam & Penilaian Skor --
    print("   -> Langkah 1: Meminta AI melakukan analisis & skoring...")
    keywords_for_summary = [TIPE_KEPRIBADIAN, KOGNITIF_UTAMA_KEY]
    specific_context_es = extract_relevant_data(bank_data, keywords_for_summary)

    prompt_step1 = PROMPT_TEMPLATES["prompt_step1_deep_analysis_and_score"].format(
        specific_context=specific_context_es,
        tipe_kepribadian=TIPE_KEPRIBADIAN,
        pekerjaan=PEKERJAAN,
        kognitif_utama=kognitif_utama_display_name
    )
    deep_analysis_output = generate_ai_content(prompt_step1, model=MODEL_AI, task_name="ES - Analisis & Skor")

    executive_summary_formatted = "Konten Executive Summary gagal digenerate."

    if "Error:" not in deep_analysis_output:
        # -- Langkah 2: Penentuan Level Kecocokan --
        print("   -> Langkah 2: Meminta AI menentukan level kecocokan...")
        prompt_step2 = PROMPT_TEMPLATES["prompt_step2_determine_level"].format(
            deep_analysis_and_score=deep_analysis_output
        )
        determined_level = generate_ai_content(prompt_step2, model=MODEL_AI, task_name="ES - Penentuan Level").strip()

        if "Error:" not in determined_level and determined_level:
            # -- Langkah 3: Penulisan Narasi Final --
            print(f"   -> Langkah 3: AI menentukan level: '{determined_level}'. Meminta penulisan narasi...")
            prompt_step3 = PROMPT_TEMPLATES["prompt_step3_write_narrative"].format(
                determined_level=determined_level,
                deep_analysis_and_score=deep_analysis_output
            )
            executive_summary_formatted = generate_ai_content(prompt_step3, model=MODEL_AI, task_name="ES - Penulisan Narasi")

            if "Error:" not in executive_summary_formatted:
                # Konversi Markdown ke HTML
                # Gunakan .replace() untuk mengganti teks literal. Jauh lebih aman dan sederhana.
                executive_summary_formatted = executive_summary_formatted.replace('**Executive Summary**', '').strip()                  
                executive_summary_formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', executive_summary_formatted)
                print("   -- Executive Summary otomatis yang detail berhasil dibuat.")
            else:
                print(f"   -- Gagal pada langkah penulisan narasi. Respon: {executive_summary_formatted}")
        else:
            print(f"   -- Gagal pada langkah penentuan level. Respon: {determined_level}")
    else:
        print(f"   -- Gagal pada langkah analisis awal. Respon: {deep_analysis_output}")

    # === LANGKAH 2: GENERATE PERSON-JOB FIT (DENGAN KONVERSI MARKDOWN KE HTML) ===
    print("2. Menggenerate konten Person-Job Fit dalam format Markdown...")
    prompt_job_fit = PROMPT_TEMPLATES["person_job_fit_full"].format(
        tipe_kepribadian=TIPE_KEPRIBADIAN,
        kognitif_utama=kognitif_utama_display_name,
        specific_context=specific_context_es
    )
    # AI akan menghasilkan teks dengan format Markdown
    raw_markdown_text = generate_ai_content(prompt_job_fit, model=MODEL_AI, task_name="Person-Job Fit (Markdown)")

    if "Error:" not in raw_markdown_text:
        print("   -- Mengonversi format Markdown ke HTML untuk PDF...")
        try:
            # 1. Ubah **teks tebal** menjadi <b>teks tebal</b>
            html_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', raw_markdown_text)
            
            # 2. Ganti setiap baris baru dengan tag <br/> agar menjadi daftar
            person_fit_job_formatted = html_text.replace('\n', '<br/>')
            
            print("   -- Format HTML untuk Person-Job Fit berhasil dibuat.")
        except Exception as e:
            person_fit_job_formatted = f"Error saat konversi Markdown: {e}<br/>Teks mentah: {raw_markdown_text}"
            print(f"   -- Error saat konversi Markdown: {e}")
    else:
        person_fit_job_formatted = raw_markdown_text
        print(f"   -- Gagal meng-generate konten Person-Job Fit. Respon: {person_fit_job_formatted}")


    # === LANGKAH 3: PEMBUATAN PDF ===
    print(f"\n--- Memulai Pembuatan PDF: {NAMA_FILE_OUTPUT} ---")
    c = canvas.Canvas(NAMA_FILE_OUTPUT, pagesize=A4)

    # Memanggil fungsi untuk setiap halaman dengan penomoran yang benar
    halaman_1_cover(c, biodata, executive_summary_formatted, page_num=1)
    halaman_2(c, behavior_traits_text, "topoplot1.png", judul_topoplot1, page_num=2)
    halaman_3(c, behavior_traits_text_2, page_num=3)
    halaman_4(c, cognitive_traits_text, page_num=4)
    halaman_5(c, cognitive_traits_text_2, "topoplot2.png", judul_topoplot2, page_num=5)
    halaman_person_fit_job(c, person_fit_job_formatted, page_num=6)
    # Halaman 7 kosong, langsung ke Referensi di halaman 8
    # Fungsi halaman_8 akan mengurus penomoran selanjutnya jika referensi lebih dari 1 halaman
    halaman_8(c, referensi_text_1, page_num=7) 
    # Disclaimer ditempatkan di halaman terakhir, kita asumsikan halaman 12
    halaman_11(c, disclaimer_text, page_num=12) 

    c.save()
    print(f"\n✅ PDF '{NAMA_FILE_OUTPUT}' berhasil dibuat!")