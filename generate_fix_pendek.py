# filename: generate_fix_pendek.py

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color, black, white, HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase.pdfmetrics import stringWidth

import requests
import re
import os # Import os for file operations

PAGE_WIDTH, PAGE_HEIGHT = A4

# ==============================================================================
# === FUNGSI BANTUAN (Tidak ada perubahan) ===
# ==============================================================================

def markdown_to_html_platypus(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = text.replace('**', '')
    return text

def generate_ai_content(prompt, model="llama3.1:8b", task_name="AI Task"):
    try:
        print(f"-> Mengirim request untuk '{task_name}' ke model {model}...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model, "prompt": prompt, "stream": False,
                "options": { "temperature": 0.2, "top_p": 0.9, "num_predict": 2048, "repeat_penalty": 1.2 }
            },
            timeout=600
        )
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "").strip()
            if not generated_text: return f"Error: Model tidak menghasilkan response."
            print(f"   -- Berhasil meng-generate '{task_name}'.")
            return generated_text
        return f"Error: HTTP {response.status_code} - {response.text}"
    except requests.exceptions.ConnectionError:
        return "Error: Tidak bisa connect ke Ollama server."
    except Exception as e:
        return f"Error saat generate {task_name}: {str(e)}"

def extract_relevant_data(full_text, keywords):
    # This function had an issue with regex, using a simpler and more robust string finding method
    all_headings = [
        "Openess", "Conscientiousness", "Extraversion",
        "Agreeableness", "Neuroticism", "Kraepelin Test (Numerik)",
        "WCST (Logika)", "Digit Span (Short Term Memory)"
    ]

    extracted_chunks = []
    full_text_lower = full_text.lower()
    for keyword in keywords:
        try:
            start_pos = full_text_lower.find(keyword.lower())
            if start_pos == -1:
                print(f"Peringatan: Keyword '{keyword}' tidak ditemukan di bank_data.txt")
                continue

            # Find the end position by looking for the next heading
            end_pos = len(full_text)
            for heading in all_headings:
                # Find the next heading after the current keyword's position
                next_heading_pos = full_text_lower.find(heading.lower(), start_pos + len(keyword))
                if next_heading_pos != -1:
                    end_pos = min(end_pos, next_heading_pos)
            
            # Extract the content from the start of the keyword to the start of the next heading
            chunk = full_text[start_pos:end_pos].strip()
            # Get the text content after the keyword itself
            content_after_keyword = chunk[len(keyword):].strip()
            extracted_chunks.append(content_after_keyword)

        except Exception as e:
            print(f"Error saat extract data untuk keyword '{keyword}': {e}")
            
    return "\n\n".join(extracted_chunks)

# ==============================================================================
# === FUNGSI LOGIKA AI UTAMA (Tidak ada perubahan) ===
# ==============================================================================
def generate_short_report_analysis(tipe_kepribadian, kognitif_utama, pekerjaan, model_ai, bank_data_text):
    print("\nMemulai analisis AI (Metode Dynamic Master Analysis)...")
    default_error_result = {"suitability": "ANALISIS GAGAL", "reasons": ["-"], "suggestions": ["-"], "tips": "-"}

    specific_context = extract_relevant_data(bank_data_text, [tipe_kepribadian, kognitif_utama])
    if not specific_context: specific_context = "Tidak ada data konteks."

    # --- LANGKAH 1: Membuat Master Analysis ---
    prompt_master = f"""
        Anda adalah seorang analis psikologi.
        TUGAS: Tulis analisis mendalam (2-3 paragraf) tentang profil kandidat untuk posisi yang ditentukan. Fokus pada kekuatan, kelemahan, dan potensi pengembangan. Analisis ini akan menjadi dasar untuk ringkasan selanjutnya.
        PROFIL: Kepribadian {tipe_kepribadian}, Kognitif {kognitif_utama}.
        POSISI: {pekerjaan}.
        KONTEKS DATA:
        ---
        {specific_context}
        ---
    """
    master_analysis = generate_ai_content(prompt_master, model=model_ai, task_name="Langkah 1: Master Analysis")
    if "Error:" in master_analysis: return default_error_result
    
    # --- LANGKAH 2: Menentukan Level Kecocokan ---
    prompt_level = f"""
        Berdasarkan teks analisis berikut, pilih SATU level kecocokan.
        ANALISIS: "{master_analysis}"
        PILIHAN: SANGAT COCOK, COCOK DENGAN CATATAN PENGEMBANGAN, KURANG COCOK.
        Jawaban Anda harus HANYA SATU dari tiga pilihan tersebut.
    """
    determined_level_raw = generate_ai_content(prompt_level, model=model_ai, task_name="Langkah 2: Penentuan Level")
    
    cleaned_level = determined_level_raw.strip().lstrip('-* ').rstrip('.,').upper().replace("SESUAI", "COCOK")
    valid_levels = ["SANGAT COCOK", "KURANG COCOK", "COCOK DENGAN CATATAN PENGEMBANGAN"]
    
    if cleaned_level not in valid_levels:
        # Fallback to check if the response contains one of the valid levels
        found = False
        for level in valid_levels:
            if level in cleaned_level:
                cleaned_level = level
                found = True
                break
        if not found:
            print(f"!!! Peringatan: Level dari AI tidak valid ('{determined_level_raw}'). Menggunakan fallback.")
            # Simple fallback based on master analysis content
            if "sangat cocok" in master_analysis.lower() or "sangat positif" in master_analysis.lower():
                cleaned_level = "SANGAT COCOK"
            elif "kurang cocok" in master_analysis.lower() or "risiko signifikan" in master_analysis.lower():
                cleaned_level = "KURANG COCOK"
            else:
                cleaned_level = "COCOK DENGAN CATATAN PENGEMBANGAN"

    determined_level = cleaned_level

    # --- LANGKAH 3: Ekstrak Alasan ---
    prompt_reasons = f"""
        Berdasarkan teks analisis berikut, individu dinilai '{determined_level}' untuk pekerjaan tersebut.
        ANALISIS: "{master_analysis}"
        TUGAS: Identifikasi 4 alasan utama berupa kekuatan atau sifat positif yang mendukung penilaian tersebut.
        INSTRUKSI PENULISAN:
        1. Tulis dalam format daftar singkat (4 poin).
        2. Setiap poin harus sangat ringkas, **maksimal 8 kata**.
        3. Gunakan **bahasa sederhana** yang mudah dipahami orang awam.
        4. **Hindari jargon teknis**.
        5. Jangan sertakan kalimat pembuka atau penutup.
    """
    reasons_text = generate_ai_content(prompt_reasons, model=model_ai, task_name="Langkah 3: Ekstrak Alasan")
    if "Error:" in reasons_text: return default_error_result
    
    # --- LANGKAH 4: Ekstrak Saran Pengembangan ---
    prompt_suggestions = f"""
        Berdasarkan teks analisis berikut, berikan 4 hal yang dapat dilakukan untuk pengembangan diri.
        ANALISIS: "{master_analysis}"
        TUGAS: Ekstrak 4 saran pengembangan yang paling actionable.
        INSTRUKSI PENULISAN:
        1. Tulis dalam format daftar singkat (4 poin).
        2. Setiap poin harus sangat ringkas, **maksimal 8 kata**.
        3. Gunakan **bahasa sederhana** dan hindari jargon teknis.
        4. **Jangan sertakan kalimat pembuka atau penutup**.
    """
    suggestions_text = generate_ai_content(prompt_suggestions, model=model_ai, task_name="Langkah 4: Ekstrak Saran")
    if "Error:" in suggestions_text: return default_error_result
    
    # --- LANGKAH 5: Ekstrak Kesimpulan ---
    prompt_tips = f"""
        Berdasarkan analisis mendalam berikut, berikan satu saran praktis atau "tips pamungkas" yang bisa langsung diterapkan oleh individu ini untuk sukses dalam pekerjaannya, dengan mempertimbangkan kekuatan dan kelemahannya.
        ANALISIS: "{master_analysis}"
        TUGAS: Tuliskan dalam satu kalimat yang inspiratif dan actionable, **maksimal 20 kata**.
    """
    tips_text = generate_ai_content(prompt_tips, model=model_ai, task_name="Langkah 5: Ekstrak Kesimpulan")
    if "Error:" in tips_text: return default_error_result

    reasons_cleaned = [re.sub(r'^[-\*\d\.\s\\]+', '', line).strip() for line in reasons_text.split('\n') if line.strip()]
    suggestions_cleaned = [re.sub(r'^[-\*\d\.\s\\]+', '', line).strip() for line in suggestions_text.split('\n') if line.strip()]

    final_data = {
        "suitability": determined_level,
        "reasons": reasons_cleaned,
        "suggestions": suggestions_cleaned,
        "tips": tips_text.strip()
    }
    print("\nAnalisis AI dengan metode Dynamic Master Analysis selesai.")
    return final_data

def generate_job_fit_data(full_job_fit_html_text, model_ai):
    """
    FUNGSI YANG DIUBAH TOTAL:
    Menerima teks HTML rekomendasi pekerjaan yang sudah jadi, lalu meminta AI
    untuk mengekstrak dan meringkas alasannya.
    """
    print("\nMemulai peringkasan AI untuk Rekomendasi Pekerjaan...")
    
    # Jika input kosong atau error, kembalikan data default
    if not full_job_fit_html_text or "Error:" in full_job_fit_html_text:
        return [{"title": "Analisis Gagal", "reason": "Data sumber tidak tersedia."}] * 6

    # Hilangkan tag HTML untuk mempermudah AI membaca
    plain_text = re.sub('<[^<]+?>', '', full_job_fit_html_text)

    # Prompt baru yang fokus pada ekstraksi dan peringkasan
    prompt_summarize_jobs = f"""
        Anda adalah AI yang sangat ahli dalam mengekstrak dan meringkas informasi.
        
        TUGAS: Dari teks di bawah ini, identifikasi 6 judul pekerjaan beserta penjelasannya. Kemudian, tulis ulang penjelasannya menjadi alasan yang sangat singkat (maksimal 15 kata per alasan).
        
        TEKS SUMBER:
        ---
        {plain_text}
        ---
        
        FORMAT OUTPUT WAJIB (Ikuti dengan persis):
        [Nama Pekerjaan 1]: [Alasan singkat hasil ringkasan]
        [Nama Pekerjaan 2]: [Alasan singkat hasil ringkasan]
        [Nama Pekerjaan 3]: [Alasan singkat hasil ringkasan]
        [Nama Pekerjaan 4]: [Alasan singkat hasil ringkasan]
        [Nama Pekerjaan 5]: [Alasan singkat hasil ringkasan]
        [Nama Pekerjaan 6]: [Alasan singkat hasil ringkasan]
        
        ATURAN:
        - **PERTAHANKAN judul pekerjaan asli dari teks sumber**.
        - Jangan berikan nomor atau bullet point.
        - Pastikan ada 6 baris output.
    """
    
    raw_text = generate_ai_content(prompt_summarize_jobs, model=model_ai, task_name="Peringkasan Rekomendasi Pekerjaan")

    if "Error:" in raw_text:
        return [{"title": "Analisis Gagal", "reason": raw_text}] * 6

    recommendations = []
    lines = raw_text.strip().split('\n')
    for line in lines:
        if ':' in line:
            parts = line.split(':', 1)
            title = parts[0].strip().lstrip('*- ')
            reason = parts[1].strip()
            if title and reason:
                recommendations.append({"title": title, "reason": reason})

    while len(recommendations) < 6:
        recommendations.append({"title": "Data Tidak Tersedia", "reason": "AI tidak memberikan data yang cukup."})
    
    print("Peringkasan Rekomendasi Pekerjaan selesai.")
    return recommendations[:6]

# ==============================================================================
# === FUNGSI-FUNGSI GAMBAR PDF (Tidak ada perubahan signifikan) ===
# ==============================================================================

def draw_watermark(c, watermark_path):
    try:
        img = ImageReader(watermark_path)
        iw, ih = img.getSize()
        w_target, h_target = 130 * mm, (130 * mm) * ih / iw
        x, y = (PAGE_WIDTH - w_target) / 2, (PAGE_HEIGHT - h_target) / 2
        c.saveState()
        c.drawImage(img, x, y, width=w_target, height=h_target, mask='auto')
        c.restoreState()
    except Exception as e:
        print(f"⚠️ Watermark gagal dimuat: {e}")

def draw_header(c, logo_path="cia.png", is_cover=False):
    try:
        img = ImageReader(logo_path)
        iw, ih = img.getSize()
        w_target, h_target = 50 * mm, (50 * mm) * ih / iw
        x, y = 20 * mm, PAGE_HEIGHT - h_target - 10 * mm
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
    c.setFillColor(black)
    c.drawRightString(PAGE_WIDTH - 10 * mm, 10 * mm, f"{page_num}")

def draw_centered_image(c, img_path, y_top, width_mm):
    try:
        image = ImageReader(img_path)
        iw, ih = image.getSize()
        width, height = width_mm * mm, (width_mm * mm) * ih / iw
        x, y = (PAGE_WIDTH - width) / 2, y_top - height
        c.drawImage(img_path, x, y, width=width, height=height, mask='auto')
        return y
    except Exception as e:
        print(f"Gambar '{img_path}' tidak ditemukan atau error: {e}")
        return y_top - 100

def wrap_text_to_width(text, font_name, font_size, max_width_mm):
    if not text or not text.strip(): return [""]
    max_width_points = max_width_mm * mm
    words, lines, current_line = text.split(), [], ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        test_width = stringWidth(test_line, font_name, font_size)
        if test_width <= max_width_points:
            current_line = test_line
        else:
            if current_line: lines.append(current_line)
            word_width = stringWidth(word, font_name, font_size)
            if word_width > max_width_points:
                char_line = ""
                for char in word:
                    test_char = char_line + char
                    if stringWidth(test_char, font_name, font_size) <= max_width_points:
                        char_line = test_char
                    else:
                        if char_line: lines.append(char_line)
                        char_line = char
                current_line = char_line
            else:
                current_line = word
    if current_line: lines.append(current_line)
    return lines if lines else [""]

def halaman_1_cover(c, biodata, topoplot_behavior, topoplot_cognitive, tipe_kepribadian, kognitif_nama, page_num):
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
    c.setFont("Times-Bold", 12)
    
    y = draw_centered_image(c, topoplot_behavior, y - 40, 150)
    c.setFont("Times-Bold", 11)
    nama = biodata.get("Nama", "Kandidat")
    
    # Judul dinamis
    kognitif_nama_inti = kognitif_nama.split('(')[0].strip()
    c.drawCentredString(PAGE_WIDTH / 2, y - 10, f"Gambar 1. Topografi respons {nama} terhadap stimulus behavioral trait {tipe_kepribadian.lower()}")
    
    y = draw_centered_image(c, topoplot_cognitive, y - 40, 150)
    c.drawCentredString(PAGE_WIDTH / 2, y - 10, f"Gambar 2. Brain topografi Brain Wave Analysis Power stimulus {kognitif_nama_inti.lower()}")
    
    draw_footer(c, page_num)
    c.showPage()
    
def halaman_2_traits(c, data, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)
    
    # ===============================
    # Set Warna (sesuai gambar referensi)
    # ===============================
    biru_vibrant = HexColor("#1E88E5")  # Biru cerah seperti gambar
    kuning_gold = HexColor("#FCD116")  # Kuning gold awal
    kuning_muda = HexColor("#FFF2CC")
    merah_muda = HexColor("#FCE4D6")
    
    # ===============================
    # Warna Border (lebih gelap dari warna box)
    # ===============================
    biru_border = HexColor("#1565C0")  # Lebih gelap dari biru_vibrant
    kuning_border = HexColor("#D4A914")  # Lebih gelap dari kuning_gold
    kuning_muda_border = HexColor("#D4C299")  # Lebih gelap dari kuning_muda
    merah_muda_border = HexColor("#D4BBA3")  # Lebih gelap dari merah_muda
    
    # Styles for content
    styles = getSampleStyleSheet()
    style_alasan = ParagraphStyle(name='alasan', parent=styles['Normal'], fontName='Times-Roman', fontSize=10, leading=14)
    style_saran = ParagraphStyle(name='saran', parent=styles['Normal'], fontName='Times-Roman', fontSize=10, leading=14)
    style_tips = ParagraphStyle(name='tips', parent=styles['Normal'], fontName='Times-Roman', fontSize=11, leading=14, alignment=TA_CENTER, textColor=white)

    # ===============================
    # KONSISTEN SPACING & DYNAMIC BOX SIZING
    # ===============================
    consistent_gap = 7 * mm
    box_width = 78 * mm  # Sedikit lebih lebar dari original
    box_gap = 5 * mm     # Gap lebih kecil untuk lebih rapat
    start_x = (PAGE_WIDTH - (2 * box_width + box_gap)) / 2
    start_y = 250 * mm
    
    # Dynamic height calculation untuk trait boxes
    min_box_height = 50 * mm
    
    # Calculate height for Box 1
    p1_temp = Paragraph(data['trait_1_desc'], ParagraphStyle(name='temp1', textColor=white, fontName='Times-Roman', fontSize=10, leading=12))
    w1, h1 = p1_temp.wrapOn(c, box_width - 30, 100*mm)
    box1_height = max(min_box_height, h1 + 35)  # 35 untuk header + padding
    
    # Calculate height for Box 2
    p2_temp = Paragraph(data['trait_2_desc'], ParagraphStyle(name='temp2', textColor=white, fontName='Times-Roman', fontSize=10, leading=12))
    w2, h2 = p2_temp.wrapOn(c, box_width - 30, 100*mm)
    box2_height = max(min_box_height, h2 + 35)  # 35 untuk header + padding
    
    # ===============================
    # BOX 1 - Dynamic height dengan border
    # ===============================
    c.setFillColor(biru_vibrant)
    c.setStrokeColor(biru_border)
    c.setLineWidth(1.5)
    c.roundRect(start_x, start_y - box1_height, box_width, box1_height, 5*mm, fill=1, stroke=1)
    
    # Label Gambar 1
    label_width, label_height = 70, 20
    label_x = start_x + (box_width - label_width) / 2
    label_y = start_y - 15
    c.setFillColor(kuning_gold)
    c.setStrokeColor(kuning_border)
    c.setLineWidth(1)
    c.rect(label_x, label_y, label_width, label_height, fill=1, stroke=1)
    
    c.setFillColor(black)
    c.setFont("Times-Bold", 12)
    c.drawCentredString(start_x + box_width/2, label_y + 4, "Gambar 1")
    
    # Content Box 1
    c.setFillColor(white)
    c.setFont("Times-Bold", 12)
    title_text = f"✓ {data['trait_1_title']}"
    title_width = c.stringWidth(title_text, "Times-Bold", 12)
    title_x = start_x + (box_width - title_width) / 2
    c.drawString(title_x, start_y - 28, title_text)
    
    # Description Box 1
    p1 = Paragraph(data['trait_1_desc'], ParagraphStyle(name='desc1', textColor=white, fontName='Times-Roman', fontSize=10, leading=12, alignment=TA_CENTER))
    p1.wrapOn(c, box_width - 30, box1_height - 40)
    p1.drawOn(c, start_x + 15, start_y - 40 - p1.height)
    
    # ===============================
    # BOX 2 - Dynamic height dengan border
    # ===============================
    x2 = start_x + box_width + box_gap
    c.setFillColor(biru_vibrant)
    c.setStrokeColor(biru_border)
    c.setLineWidth(1.5)
    c.roundRect(x2, start_y - box2_height, box_width, box2_height, 5*mm, fill=1, stroke=1)
    
    # Label Gambar 2
    label_x2 = x2 + (box_width - label_width) / 2
    c.setFillColor(kuning_gold)
    c.setStrokeColor(kuning_border)
    c.setLineWidth(1)
    c.rect(label_x2, label_y, label_width, label_height, fill=1, stroke=1)
    
    c.setFillColor(black)
    c.setFont("Times-Bold", 12)
    c.drawCentredString(x2 + box_width/2, label_y + 4, "Gambar 2")
    
    # Content Box 2
    c.setFillColor(white)
    c.setFont("Times-Bold", 12)
    title_text2 = f"✓ {data['trait_2_title']}"
    title_width2 = c.stringWidth(title_text2, "Times-Bold", 12)
    title_x2 = x2 + (box_width - title_width2) / 2
    c.drawString(title_x2, start_y - 28, title_text2)
    
    # Description Box 2
    p2 = Paragraph(data['trait_2_desc'], ParagraphStyle(name='desc2', textColor=white, fontName='Times-Roman', fontSize=10, leading=12, alignment=TA_CENTER))
    p2.wrapOn(c, box_width - 30, box2_height - 40)
    p2.drawOn(c, x2 + 15, start_y - 40 - p2.height)

    # ===============================
    # DYNAMIC POSITIONING - Box selanjutnya mengikuti box terpanjang
    # ===============================
    max_box_height = max(box1_height, box2_height)
    suitability_y_top = start_y - max_box_height - consistent_gap
    
    # Calculate dynamic height untuk suitability box
    temp_y = suitability_y_top - 40
    total_reasons_height = 0
    for i, reason_md in enumerate(data['reasons']):
        reason_html = markdown_to_html_platypus(reason_md)
        p_temp = Paragraph(f"{i+1}. {reason_html}", style_alasan)
        w, h = p_temp.wrapOn(c, 150*mm, 20*mm)
        total_reasons_height += (h + 4)
    
    suitability_height = max(65*mm, total_reasons_height + 40*mm)  # 40mm untuk header + padding
    
    # ===============================
    # BOX SUITABILITY - dengan transparansi dan border
    # ===============================
    c.setFillColorRGB(255/255, 242/255, 204/255, alpha=0.85)  # Kuning muda dengan transparansi
    c.setStrokeColor(kuning_muda_border)
    c.setLineWidth(1.5)
    c.roundRect(25*mm, suitability_y_top - suitability_height, 160*mm, suitability_height, 5*mm, fill=1, stroke=1)
    
    c.setFillColor(black)
    c.setFont("Times-Bold", 12)
    c.drawCentredString(105*mm, suitability_y_top - 20, f"■ {data['suitability']} untuk posisi")
    c.drawCentredString(105*mm, suitability_y_top - 35, data["position"])
    
    # Alasan content
    c.setFont("Times-Bold", 12)
    c.drawString(35*mm, suitability_y_top - 55, "Alasan :")
    
    y = suitability_y_top - 70
    for i, reason_md in enumerate(data['reasons']):
        reason_html = markdown_to_html_platypus(reason_md)
        p = Paragraph(f"{i+1}. {reason_html}", style_alasan)
        w, h = p.wrapOn(c, 150*mm, 20*mm)
        p.drawOn(c, 30*mm, y-h)
        y -= (h + 4)

    # ===============================
    # BOX PENGEMBANGAN - Dynamic positioning dengan transparansi
    # ===============================
    pengembangan_y_top = suitability_y_top - suitability_height - consistent_gap
    
    # Calculate dynamic height untuk pengembangan box
    total_suggestions_height = 0
    for suggestion_md in data['suggestions']:
        suggestion_html = markdown_to_html_platypus(suggestion_md)
        p_temp = Paragraph(f"• {suggestion_html}", style_saran)
        w, h = p_temp.wrapOn(c, 150*mm, 20*mm)
        total_suggestions_height += (h + 4)
    
    pengembangan_height = max(48*mm, total_suggestions_height + 30*mm)  # 30mm untuk header + padding
    
    c.setFillColorRGB(252/255, 228/255, 214/255, alpha=0.85)  # Merah muda dengan transparansi
    c.setStrokeColor(merah_muda_border)
    c.setLineWidth(1.5)
    c.roundRect(25*mm, pengembangan_y_top - pengembangan_height, 160*mm, pengembangan_height, 5*mm, fill=1, stroke=1)
    
    c.setFillColor(black)
    c.setFont("Times-Bold", 13)
    c.drawCentredString(105*mm, pengembangan_y_top - 20, "Pengembangan yang Harus Dilakukan")
    
    y = pengembangan_y_top - 35
    for suggestion_md in data['suggestions']:
        suggestion_html = markdown_to_html_platypus(suggestion_md)
        p = Paragraph(f"• {suggestion_html}", style_saran)
        w, h = p.wrapOn(c, 150*mm, 20*mm)
        p.drawOn(c, 30*mm, y-h)
        y -= (h + 4)

    # ===============================
    # BOX TIPS - Dynamic positioning
    # ===============================
    tips_y_top = pengembangan_y_top - pengembangan_height - consistent_gap
    
    # Calculate tips height
    tips_html = markdown_to_html_platypus(data['tips'])
    p_tips_temp = Paragraph(f'{tips_html}', style_tips)
    w_tips, h_tips = p_tips_temp.wrapOn(c, 150*mm, 20*mm)
    tips_height = max(25*mm, h_tips + 10*mm)  # 10mm padding
    
    # Safety check: minimal 25mm dari footer
    min_y_from_bottom = 25 * mm
    calculated_bottom = tips_y_top - tips_height
    if calculated_bottom < min_y_from_bottom:
        tips_y_top = min_y_from_bottom + tips_height

    c.setFillColor(biru_vibrant)
    c.setStrokeColor(biru_border)
    c.setLineWidth(1.5)
    c.roundRect(25*mm, tips_y_top - tips_height, 160*mm, tips_height, 5*mm, fill=1, stroke=1)
    
    # Tips content - centered vertically
    p_tips = Paragraph(f'"{tips_html}"', style_tips)
    w_tips, h_tips = p_tips.wrapOn(c, 150*mm, tips_height - 10*mm)
    p_tips.drawOn(c, (PAGE_WIDTH-w_tips)/2, tips_y_top - (tips_height + h_tips)/2)

    draw_footer(c, page_num)
    c.showPage()
        
def halaman_3_job_fit(c, job_data, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)
    c.setFont("Times-Bold", 14)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 150, "PERSON TO FIT BIDANG KERJA/USAHA")
    
    box_width, h_gap, v_gap = 88 * mm, 10 * mm, 10 * mm
    total_row_width = (2 * box_width) + h_gap
    x_start = (PAGE_WIDTH - total_row_width) / 2
    y_start = PAGE_HEIGHT - 170
    
    font_name, font_size, line_height = "Times-Roman", 11, 12
    padding_top, padding_bottom, min_box_height = 20, 12, 45 * mm
    text_width_mm = (box_width - 15) / mm
    box_data = []
    for job in job_data:
        wrapped = wrap_text_to_width(job['reason'], font_name, font_size, text_width_mm)
        num_lines = len(wrapped)
        content_height_points = padding_top + (num_lines * line_height) + padding_bottom
        dynamic_height = max(min_box_height, content_height_points)
        box_data.append({"job": job, "wrapped": wrapped, "height": dynamic_height})
    y_cursor = y_start
    for row in range(0, len(box_data), 2):
        row_items = box_data[row:row+2]
        if not row_items: continue
        max_row_height = max(item["height"] for item in row_items)
        for col, item in enumerate(row_items):
            x, y = x_start + col * (box_width + h_gap), y_cursor
            c.saveState()
            c.setFillColor(Color(0.88, 0.94, 0.85, alpha=0.8))
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(x, y - item["height"], box_width, item["height"], fill=1, stroke=1)
            c.restoreState()
            text_x, text_y, job = x + 10, y - padding_top, item["job"]
            c.setFont("Times-Bold", 12)
            c.setFillColor(black)
            c.drawString(text_x, text_y, f"{job['title']}")
            c.setFont("Times-Bold", 11)
            c.drawString(text_x, text_y - 15, "Alasan:")
            c.setFont(font_name, font_size)
            for i_line, line in enumerate(item["wrapped"]):
                line_y = text_y - 30 - (i_line * line_height)
                if line_y < (y - item["height"] + padding_bottom): break
                c.drawString(text_x, line_y, line)
        y_cursor -= max_row_height + v_gap
    draw_footer(c, page_num)
    c.showPage()

def halaman_4_disclaimer(c, disclaimer_text, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)
    c.setFont("Times-Bold", 12)
    c.setFillColor(black)
    c.drawString(20 * mm, PAGE_HEIGHT - 150, "Disclaimer")
    left_margin, right_margin, top_margin = 20 * mm, 20 * mm, PAGE_HEIGHT - 170
    text_width = PAGE_WIDTH - left_margin - right_margin
    style = ParagraphStyle(name='Justified', fontName='Times-Roman', fontSize=10, leading=15, alignment=TA_JUSTIFY)
    text_for_paragraph = disclaimer_text.replace('\n', ' ').replace('  ', ' ')
    p = Paragraph(text_for_paragraph, style)
    w, h = p.wrapOn(c, text_width, PAGE_HEIGHT)
    p.drawOn(c, left_margin, top_margin - h)
    draw_footer(c, page_num)
    c.showPage()
    
# =======================================================
# === FUNGSI UTAMA UNTUK GENERATE LAPORAN PENDEK (BARU) ===
# =======================================================
def generate_short_report(
    tipe_kepribadian,
    kognitif_utama_key,
    pekerjaan,
    model_ai,
    nama_file_output,
    biodata_kandidat,
    topoplot_path_behaviour,
    topoplot_path_cognitive,
    personality_title,
    personality_desc,
    cognitive_title,
    cognitive_desc,
    person_job_fit_text_from_long_report: str
):
    """Fungsi utama untuk menggenerate laporan profiling pendek dari awal hingga akhir."""
    
    print("\n--- Memulai Pembuatan Laporan Pendek ---")

    # --------------------------------------------------------------------------
    # A: MEMUAT DATA BANK UNTUK KONTEKS AI
    # --------------------------------------------------------------------------
    try:
        with open("bank_data.txt", "r", encoding="utf-8") as f:
            bank_data_content = f.read()
        print("File 'bank_data.txt' untuk laporan pendek berhasil dimuat.")
    except FileNotFoundError:
        print("Error: file 'bank_data.txt' tidak ditemukan! Konteks AI akan kosong.")
        bank_data_content = ""
    
    # --------------------------------------------------------------------------
    # B: GENERATE DATA DINAMIS DARI AI
    # --------------------------------------------------------------------------
    # Generate data untuk Halaman 2 (Analisis Kecocokan)
    ai_analysis_data = generate_short_report_analysis(
        tipe_kepribadian=tipe_kepribadian,
        kognitif_utama=kognitif_utama_key,
        pekerjaan=pekerjaan,
        model_ai=model_ai,
        bank_data_text=bank_data_content
    )

    # Generate data untuk Halaman 3 (Rekomendasi Pekerjaan)
    job_fit_data = generate_job_fit_data(
        full_job_fit_html_text=person_job_fit_text_from_long_report,
        model_ai=model_ai
    )

    # --------------------------------------------------------------------------
    # C: PERSIAPAN DATA UNTUK PDF
    # --------------------------------------------------------------------------
    
    # Data untuk halaman 2, sekarang menggunakan data dinamis yang di-pass
    personality_data_for_pdf = {
        "trait_1_title": personality_title,
        "trait_1_desc": personality_desc,
        "trait_2_title": cognitive_title,
        "trait_2_desc": cognitive_desc,
        "position": pekerjaan,
        "suitability": ai_analysis_data.get('suitability', 'ANALISIS GAGAL'),
        "reasons": ai_analysis_data.get('reasons', ['- Gagal mendapatkan alasan.']),
        "suggestions": ai_analysis_data.get('suggestions', ['- Gagal mendapatkan saran.']),
        "tips": ai_analysis_data.get('tips', 'Analisis Kesimpulan Gagal.')
    }
    
    # Teks disclaimer statis
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
        'dengan akurasi 81.08% dan agreeableness dengan 86.11% <u><font color="#3366cc">Rana et al., 2021</font></u>.'
    )

    # --------------------------------------------------------------------------
    # D: PEMBUATAN PDF
    # --------------------------------------------------------------------------
    c = canvas.Canvas(nama_file_output, pagesize=A4)

    halaman_1_cover(c, biodata_kandidat, topoplot_path_behaviour, topoplot_path_cognitive, tipe_kepribadian, kognitif_utama_key, page_num=1)
    halaman_2_traits(c, personality_data_for_pdf, page_num=2)
    halaman_3_job_fit(c, job_fit_data, page_num=3)
    halaman_4_disclaimer(c, disclaimer_text, page_num=4)

    c.save()
    print(f"PDF Laporan Pendek '{nama_file_output}' berhasil dibuat!")