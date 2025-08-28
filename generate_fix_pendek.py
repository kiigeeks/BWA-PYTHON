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
import os

PAGE_WIDTH, PAGE_HEIGHT = A4

class OllamaConnectionError(Exception):
    """Exception khusus untuk menandai error koneksi ke Ollama."""
    pass

# ==============================================================================
# === FUNGSI BANTUAN ===
# ==============================================================================

def markdown_to_html_platypus(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = text.replace('**', '')
    return text

def truncate_text(text, max_words):
    """Fungsi untuk memotong teks jika melebihi batas kata."""
    words = text.split()
    if len(words) > max_words:
        return ' '.join(words[:max_words]) + '...'
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
            timeout=300
        )
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "").strip()
            if not generated_text:
                # Ini juga bisa kita jadikan exception jika diinginkan, tapi return error masih oke
                return f"Error: Model tidak menghasilkan response."
            print(f"   -- Berhasil meng-generate '{task_name}'.")
            return generated_text
        
        # Melempar error untuk status HTTP yang buruk juga merupakan ide bagus
        raise OllamaConnectionError(f"Error: HTTP {response.status_code} - {response.text}")

    except requests.exceptions.ConnectionError:
        # --- PERUBAHAN 2: Ganti 'return' dengan 'raise' ---
        # Ini akan menghentikan proses dan ditangkap oleh tasks.py
        raise OllamaConnectionError("Tidak bisa terhubung ke Ollama server. Pastikan 'ollama serve' sudah berjalan.")
    except Exception as e:
        # Melempar kembali error lain sebagai exception yang lebih spesifik
        raise OllamaConnectionError(f"Error saat generate {task_name}: {str(e)}")
    
def extract_relevant_data(full_text, keywords):
    all_headings = [
        "Openess", "Conscientiousness", "Extraversion",
        "Agreeableness", "Neuroticism", "Kraepelin Test (Numerik)",
        "WCST (Logika)", "Digit Span (Short Term Memory)"
    ]
    extracted_chunks, full_text_lower = [], full_text.lower()
    for keyword in keywords:
        try:
            start_pos = full_text_lower.find(keyword.lower())
            if start_pos == -1: continue
            end_pos = len(full_text)
            for heading in all_headings:
                next_heading_pos = full_text_lower.find(heading.lower(), start_pos + len(keyword))
                if next_heading_pos != -1: end_pos = min(end_pos, next_heading_pos)
            chunk = full_text[start_pos:end_pos].strip()
            content_after_keyword = chunk[len(keyword):].strip()
            extracted_chunks.append(content_after_keyword)
        except Exception as e:
            print(f"Error saat extract data untuk keyword '{keyword}': {e}")
    return "\n\n".join(extracted_chunks)

# ==============================================================================
# === FUNGSI LOGIKA AI UTAMA ===
# ==============================================================================
def generate_short_report_analysis(tipe_kepribadian, kognitif_utama, pekerjaan, model_ai, bank_data_text):
    print("\nMemulai analisis AI (Metode Dynamic Master Analysis)...")
    specific_context = extract_relevant_data(bank_data_text, [tipe_kepribadian, kognitif_utama])
    if not specific_context: specific_context = "Tidak ada data konteks."

    prompt_suggestions_final = """
        Berdasarkan analisis profil berikut, berikan 4 rekomendasi pengembangan diri.
        ANALISIS: "{master_analysis}"
        TUGAS: Tulis 4 rekomendasi pengembangan yang **singkat dan memberikan contoh nyata**.
        INSTRUKSI WAJIB:
        1.  Tulis dalam format daftar (4 poin).
        2.  Setiap poin harus berupa kalimat perintah yang actionable.
        3.  Berikan **contoh aktivitas spesifik** di setiap poin (misal: "Gunakan aplikasi Lumosity...", "Latih teknik pencatatan Cornell...").
        4.  Panjang setiap poin **maksimal 12 kata**.
        5.  **MUTLAK: Jangan menulis kalimat pembuka**. Langsung mulai dengan poin pertama.
    """
    
    def clean_ai_list(text_list):
        boilerplate_starters = ["berikut adalah", "inilah", "ini adalah", "berikut ini"]
        cleaned_list = [line for line in text_list if not any(line.lower().strip().startswith(starter) for starter in boilerplate_starters)]
        return cleaned_list

    if not pekerjaan or not pekerjaan.strip():
        print(" -> Mode: Analisis Profil Umum (Tanpa Pekerjaan)")
        prompt_master_general = f"Anda adalah seorang psikolog ahli.\nTUGAS: Tulis analisis mendalam (2-3 paragraf) tentang profil umum individu berdasarkan kombinasi kepribadian dan kognitifnya. Fokus pada kekuatan unik dan potensi area pengembangan. JANGAN sebutkan pekerjaan atau kesesuaian kerja.\nPROFIL: Kepribadian {tipe_kepribadian}, Kognitif {kognitif_utama}.\nKONTEKS DATA:\n---\n{specific_context}\n---"
        master_analysis = generate_ai_content(prompt_master_general, model=model_ai, task_name="Langkah 1: Master Analysis (Umum)")
        
        prompt_advantages = f'Berdasarkan teks analisis profil umum berikut:\nANALISIS: "{master_analysis}"\nTUGAS: Identifikasi 4 kelebihan atau kekuatan utama dari profil individu tersebut.\nINSTRUKSI:\n1. Tulis dalam format daftar singkat (4 poin).\n2. Setiap poin ringkas, maksimal 8 kata.\n3. Gunakan bahasa sederhana dan positif.\n4. Jangan sertakan kalimat pembuka atau penutup.'
        advantages_text = generate_ai_content(prompt_advantages, model=model_ai, task_name="Langkah 2: Ekstrak Kelebihan")
        
        suggestions_text = generate_ai_content(prompt_suggestions_final.format(master_analysis=master_analysis), model=model_ai, task_name="Langkah 3: Ekstrak Saran (Umum)")
        
        prompt_tips = f"Berdasarkan analisis mendalam berikut, berikan satu saran praktis atau \"tips pamungkas\" yang bisa langsung diterapkan oleh individu ini untuk sukses secara umum, dengan mempertimbangkan kekuatan dan kelemahannya.\nANALISIS: \"{master_analysis}\"\nTUGAS: Tuliskan dalam satu kalimat inspiratif dan actionable, maksimal 20 kata."
        tips_text = generate_ai_content(prompt_tips, model=model_ai, task_name="Langkah 4: Ekstrak Kesimpulan (Umum)")

        advantages_cleaned = [re.sub(r'^[-\*\d\.\s\\]+', '', line).strip() for line in advantages_text.split('\n') if line.strip()]
        suggestions_cleaned = [re.sub(r'^[-\*\d\.\s\\]+', '', line).strip() for line in suggestions_text.split('\n') if line.strip()]

        print("Analisis AI untuk Profil Umum selesai.")
        return {
            "suitability": "Pertimbangan Berdasarkan Brain Wave Analysis",
            "position": "Analisis Profil Psikologis Umum",
            "reasons_title": "Pertimbangan:",
            "reasons": clean_ai_list(advantages_cleaned),
            "suggestions": [truncate_text(s, 12) for s in clean_ai_list(suggestions_cleaned)],
            "tips": tips_text.strip()
        }

    else:
        print(f" -> Mode: Analisis Kesesuaian untuk Pekerjaan '{pekerjaan}'")
        prompt_master = f"Anda adalah seorang analis psikologi.\nTUGAS: Tulis analisis mendalam (2-3 paragraf) tentang profil kandidat untuk posisi yang ditentukan. Fokus pada kekuatan, kelemahan, dan potensi pengembangan.\nPROFIL: Kepribadian {tipe_kepribadian}, Kognitif {kognitif_utama}.\nPOSISI: {pekerjaan}.\nKONTEKS DATA:\n---\n{specific_context}\n---"
        master_analysis = generate_ai_content(prompt_master, model=model_ai, task_name="Langkah 1: Master Analysis (Pekerjaan)")
        
        prompt_level = f'Berdasarkan teks analisis berikut, pilih SATU level kesesuaian.\nANALISIS: "{master_analysis}"\nPILIHAN: SANGAT SESUAI, SESUAI DENGAN CATATAN PENGEMBANGAN, KURANG SESUAI.\nJawaban Anda harus HANYA SATU dari tiga pilihan tersebut.'
        determined_level_raw = generate_ai_content(prompt_level, model=model_ai, task_name="Langkah 2: Penentuan Level")
        cleaned_level = determined_level_raw.strip().lstrip('-* ').rstrip('.,').upper().replace("SESUAI", "sesuai")
        valid_levels, determined_level = ["SANGAT SESUAI", "KURANG SESUAI", "SESUAI DENGAN CATATAN PENGEMBANGAN"], "SESUAI DENGAN CATATAN PENGEMBANGAN"
        if cleaned_level in valid_levels: determined_level = cleaned_level

        prompt_reasons = f'Berdasarkan teks analisis berikut, individu dinilai \'{determined_level}\' untuk pekerjaan tersebut.\nANALISIS: "{master_analysis}"\nTUGAS: Identifikasi 4 alasan utama berupa kekuatan atau sifat positif yang mendukung penilaian tersebut.\nINSTRUKSI:\n1. Tulis dalam format daftar singkat (4 poin).\n2. Setiap poin ringkas, maksimal 8 kata.\n3. Gunakan bahasa sederhana.\n4. Hindari jargon teknis.\n5. Jangan sertakan kalimat pembuka/penutup.'
        reasons_text = generate_ai_content(prompt_reasons, model=model_ai, task_name="Langkah 3: Ekstrak Alasan")
        
        suggestions_text = generate_ai_content(prompt_suggestions_final.format(master_analysis=master_analysis), model=model_ai, task_name="Langkah 4: Ekstrak Saran")
        
        prompt_tips = f"Berdasarkan analisis mendalam berikut, berikan satu saran praktis atau \"tips pamungkas\" yang bisa langsung diterapkan oleh individu ini untuk sukses dalam pekerjaannya, dengan mempertimbangkan kekuatan dan kelemahannya.\nANALISIS: \"{master_analysis}\"\nTUGAS: Tuliskan dalam satu kalimat inspiratif dan actionable, maksimal 20 kata."
        tips_text = generate_ai_content(prompt_tips, model=model_ai, task_name="Langkah 5: Ekstrak Kesimpulan")

        reasons_cleaned = [re.sub(r'^[-\*\d\.\s\\]+', '', line).strip() for line in reasons_text.split('\n') if line.strip()]
        suggestions_cleaned = [re.sub(r'^[-\*\d\.\s\\]+', '', line).strip() for line in suggestions_text.split('\n') if line.strip()]
        
        print(f"Analisis AI untuk Pekerjaan '{pekerjaan}' selesai.")
        return {
            "suitability": determined_level,
            "position": pekerjaan,
            "reasons_title": "Alasan :",
            "reasons": clean_ai_list(reasons_cleaned),
            "suggestions": [truncate_text(s, 12) for s in clean_ai_list(suggestions_cleaned)],
            "tips": tips_text.strip()
        }

def generate_job_fit_data(full_job_fit_html_text, model_ai):
    print("\nMemulai peringkasan AI untuk Rekomendasi Pekerjaan...")
    if not full_job_fit_html_text or "Error:" in full_job_fit_html_text:
        return [{"title": "Analisis Gagal", "reason": "Data sumber tidak tersedia."}] * 6
    plain_text = re.sub('<[^<]+?>', '', full_job_fit_html_text)
    prompt_summarize_jobs = f"Anda adalah AI yang sangat ahli dalam mengekstrak dan meringkas informasi.\nTUGAS: Dari teks di bawah ini, identifikasi 6 judul pekerjaan beserta penjelasannya. Kemudian, tulis ulang penjelasannya menjadi alasan yang sangat singkat (maksimal 15 kata per alasan).\nTEKS SUMBER:\n---\n{plain_text}\n---\nFORMAT OUTPUT WAJIB (Ikuti dengan persis):\n[Nama Pekerjaan 1]: [Alasan singkat hasil ringkasan]\n[Nama Pekerjaan 2]: [Alasan singkat hasil ringkasan]\n[Nama Pekerjaan 3]: [Alasan singkat hasil ringkasan]\n[Nama Pekerjaan 4]: [Alasan singkat hasil ringkasan]\n[Nama Pekerjaan 5]: [Alasan singkat hasil ringkasan]\n[Nama Pekerjaan 6]: [Alasan singkat hasil ringkasan]\nATURAN:\n- PERTAHANKAN judul pekerjaan asli dari teks sumber.\n- Jangan berikan nomor atau bullet point.\n- Pastikan ada 6 baris output."
    raw_text = generate_ai_content(prompt_summarize_jobs, model=model_ai, task_name="Peringkasan Rekomendasi Pekerjaan")
    if "Error:" in raw_text: return [{"title": "Analisis Gagal", "reason": raw_text}] * 6
    recommendations = []
    for line in raw_text.strip().split('\n'):
        if ':' in line:
            parts = line.split(':', 1)
            title, reason = parts[0].strip().lstrip('*- '), parts[1].strip()
            if title and reason: recommendations.append({"title": title, "reason": reason})
    while len(recommendations) < 6: recommendations.append({"title": "Data Tidak Tersedia", "reason": "AI tidak memberikan data yang cukup."})
    print("Peringkasan Rekomendasi Pekerjaan selesai.")
    return recommendations[:6]

# ==============================================================================
# === FUNGSI-FUNGSI GAMBAR PDF ===
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
    except Exception as e: print(f"⚠️ Watermark gagal dimuat: {e}")

def draw_header(c, logo_path="cia.png", is_cover=False):
    try:
        img = ImageReader(logo_path)
        iw, ih = img.getSize()
        w_target, h_target = 50 * mm, (50 * mm) * ih / iw
        x, y = 20 * mm, PAGE_HEIGHT - h_target - 10 * mm
        c.drawImage(img, x, y, width=w_target, height=h_target, mask='auto')
    except Exception as e: print(f"Logo gagal dimuat: {e}")
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
    max_width_points, words, lines, current_line = max_width_mm * mm, text.split(), [], ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if stringWidth(test_line, font_name, font_size) <= max_width_points: current_line = test_line
        else:
            if current_line: lines.append(current_line)
            if stringWidth(word, font_name, font_size) > max_width_points:
                char_line = ""
                for char in word:
                    if stringWidth(char_line + char, font_name, font_size) <= max_width_points: char_line += char
                    else:
                        if char_line: lines.append(char_line)
                        char_line = char
                current_line = char_line
            else: current_line = word
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
    kognitif_nama_inti = kognitif_nama.split('(')[0].strip()
    c.drawCentredString(PAGE_WIDTH / 2, y - 10, f"Gambar 1. Topografi respons {nama} terhadap stimulus behavioral trait {tipe_kepribadian.lower()}")
    y = draw_centered_image(c, topoplot_cognitive, y - 40, 150)
    c.drawCentredString(PAGE_WIDTH / 2, y - 10, f"Gambar 2. Brain topografi Brain Wave Analysis Power stimulus {kognitif_nama_inti.lower()}")
    draw_footer(c, page_num)
    c.showPage()
    
def halaman_2_traits(c, data, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)
    biru_vibrant, kuning_gold = HexColor("#1E88E5"), HexColor("#FCD116")
    biru_border, kuning_border, kuning_muda_border, merah_muda_border = HexColor("#1565C0"), HexColor("#D4A914"), HexColor("#D4C299"), HexColor("#D4BBA3")
    styles = getSampleStyleSheet()
    style_alasan = ParagraphStyle(name='alasan', parent=styles['Normal'], fontName='Times-Roman', fontSize=10, leading=14)
    style_saran = ParagraphStyle(name='saran', parent=styles['Normal'], fontName='Times-Roman', fontSize=10, leading=14)
    style_tips = ParagraphStyle(name='tips', parent=styles['Normal'], fontName='Times-Roman', fontSize=11, leading=14, alignment=TA_CENTER, textColor=white)
    consistent_gap, box_width, box_gap = 7 * mm, 78 * mm, 5 * mm
    start_x, start_y = (PAGE_WIDTH - (2 * box_width + box_gap)) / 2, 250 * mm
    p1_temp = Paragraph(data['trait_1_desc'], ParagraphStyle(name='temp1', textColor=white, fontName='Times-Roman', fontSize=10, leading=12))
    w1, h1 = p1_temp.wrapOn(c, box_width - 30, 100*mm)
    box1_height = max(50*mm, h1 + 35)
    p2_temp = Paragraph(data['trait_2_desc'], ParagraphStyle(name='temp2', textColor=white, fontName='Times-Roman', fontSize=10, leading=12))
    w2, h2 = p2_temp.wrapOn(c, box_width - 30, 100*mm)
    box2_height = max(50*mm, h2 + 35)
    c.setFillColor(biru_vibrant); c.setStrokeColor(biru_border); c.setLineWidth(1.5)
    c.roundRect(start_x, start_y - box1_height, box_width, box1_height, 5*mm, fill=1, stroke=1)
    label_x, label_y, label_width, label_height = start_x + (box_width - 70) / 2, start_y - 15, 70, 20
    c.setFillColor(kuning_gold); c.setStrokeColor(kuning_border); c.setLineWidth(1)
    c.rect(label_x, label_y, label_width, label_height, fill=1, stroke=1)
    c.setFillColor(black); c.setFont("Times-Bold", 12)
    c.drawCentredString(start_x + box_width/2, label_y + 4, "Gambar 1")
    c.setFillColor(white); c.setFont("Times-Bold", 12)
    c.drawCentredString(start_x + box_width/2, start_y - 28, f"✓ {data['trait_1_title']}")
    p1 = Paragraph(data['trait_1_desc'], ParagraphStyle(name='desc1', textColor=white, fontName='Times-Roman', fontSize=10, leading=12, alignment=TA_CENTER))
    p1.wrapOn(c, box_width - 30, box1_height - 40)
    p1.drawOn(c, start_x + 15, start_y - 40 - p1.height)
    x2 = start_x + box_width + box_gap
    c.setFillColor(biru_vibrant); c.setStrokeColor(biru_border); c.setLineWidth(1.5)
    c.roundRect(x2, start_y - box2_height, box_width, box2_height, 5*mm, fill=1, stroke=1)
    label_x2 = x2 + (box_width - 70) / 2
    c.setFillColor(kuning_gold); c.setStrokeColor(kuning_border); c.setLineWidth(1)
    c.rect(label_x2, label_y, label_width, label_height, fill=1, stroke=1)
    c.setFillColor(black); c.setFont("Times-Bold", 12)
    c.drawCentredString(x2 + box_width/2, label_y + 4, "Gambar 2")
    c.setFillColor(white); c.setFont("Times-Bold", 12)
    c.drawCentredString(x2 + box_width/2, start_y - 28, f"✓ {data['trait_2_title']}")
    p2 = Paragraph(data['trait_2_desc'], ParagraphStyle(name='desc2', textColor=white, fontName='Times-Roman', fontSize=10, leading=12, alignment=TA_CENTER))
    p2.wrapOn(c, box_width - 30, box2_height - 40)
    p2.drawOn(c, x2 + 15, start_y - 40 - p2.height)
    max_box_height = max(box1_height, box2_height)
    suitability_y_top = start_y - max_box_height - consistent_gap
    total_reasons_height = sum(Paragraph(f"{i+1}. {markdown_to_html_platypus(reason_md)}", style_alasan).wrapOn(c, 150*mm, 20*mm)[1] + 4 for i, reason_md in enumerate(data.get('reasons', [])))
    suitability_height = max(65*mm, total_reasons_height + 40*mm)
    c.setFillColorRGB(255/255, 242/255, 204/255, alpha=0.85); c.setStrokeColor(kuning_muda_border); c.setLineWidth(1.5)
    c.roundRect(25*mm, suitability_y_top - suitability_height, 160*mm, suitability_height, 5*mm, fill=1, stroke=1)
    c.setFillColor(black); c.setFont("Times-Bold", 12)
    c.drawCentredString(105*mm, suitability_y_top - 20, f"■ {data.get('suitability', '')}")
    c.drawCentredString(105*mm, suitability_y_top - 35, data.get("position", ''))
    c.setFont("Times-Bold", 12)
    c.drawString(35*mm, suitability_y_top - 55, data.get("reasons_title", ''))
    y = suitability_y_top - 70
    for i, reason_md in enumerate(data.get('reasons', [])):
        p = Paragraph(f"{i+1}. {markdown_to_html_platypus(reason_md)}", style_alasan)
        w, h = p.wrapOn(c, 150*mm, 20*mm)
        p.drawOn(c, 30*mm, y-h)
        y -= (h + 4)
    pengembangan_y_top = suitability_y_top - suitability_height - consistent_gap
    total_suggestions_height = sum(Paragraph(f"• {markdown_to_html_platypus(sug)}", style_saran).wrapOn(c, 150*mm, 20*mm)[1] + 4 for sug in data.get('suggestions', []))
    pengembangan_height = max(48*mm, total_suggestions_height + 30*mm)
    c.setFillColorRGB(252/255, 228/255, 214/255, alpha=0.85); c.setStrokeColor(merah_muda_border); c.setLineWidth(1.5)
    c.roundRect(25*mm, pengembangan_y_top - pengembangan_height, 160*mm, pengembangan_height, 5*mm, fill=1, stroke=1)
    c.setFillColor(black); c.setFont("Times-Bold", 13)
    c.drawCentredString(105*mm, pengembangan_y_top - 20, "Area Pengembangan yang Dapat Dilakukan")
    y = pengembangan_y_top - 35
    for suggestion_md in data.get('suggestions', []):
        p = Paragraph(f"• {markdown_to_html_platypus(suggestion_md)}", style_saran)
        w, h = p.wrapOn(c, 150*mm, 20*mm)
        p.drawOn(c, 30*mm, y-h)
        y -= (h + 4)
    tips_y_top = pengembangan_y_top - pengembangan_height - consistent_gap
    p_tips_temp = Paragraph(f'{markdown_to_html_platypus(data.get("tips", ""))}', style_tips)
    w_tips, h_tips = p_tips_temp.wrapOn(c, 150*mm, 20*mm)
    tips_height = max(25*mm, h_tips + 10*mm)
    c.setFillColor(biru_vibrant); c.setStrokeColor(biru_border); c.setLineWidth(1.5)
    c.roundRect(25*mm, tips_y_top - tips_height, 160*mm, tips_height, 5*mm, fill=1, stroke=1)
    p_tips = Paragraph(f'{markdown_to_html_platypus(data.get("tips", ""))}', style_tips)
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
    x_start, y_start = (PAGE_WIDTH - (2*box_width + h_gap))/2, PAGE_HEIGHT - 170
    box_data = []
    for job in job_data:
        wrapped = wrap_text_to_width(job['reason'], "Times-Roman", 11, (box_width - 15)/mm)
        content_height = 20 + (len(wrapped) * 12) + 12
        box_data.append({"job": job, "wrapped": wrapped, "height": max(45*mm, content_height)})
    y_cursor = y_start
    for row in range(0, len(box_data), 2):
        row_items = box_data[row:row+2]
        if not row_items: continue
        max_row_height = max(item["height"] for item in row_items)
        for col, item in enumerate(row_items):
            x, y = x_start + col * (box_width + h_gap), y_cursor
            c.saveState()
            c.setFillColor(Color(0.88, 0.94, 0.85, alpha=0.8)); c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(x, y - item["height"], box_width, item["height"], fill=1, stroke=1)
            c.restoreState()
            text_x, text_y = x + 10, y - 20
            c.setFont("Times-Bold", 12); c.setFillColor(black)
            c.drawString(text_x, text_y, f"{item['job']['title']}")
            c.setFont("Times-Bold", 11)
            c.drawString(text_x, text_y - 15, "Pertimbangan:")
            c.setFont("Times-Roman", 11)
            for i_line, line in enumerate(item["wrapped"]):
                line_y = text_y - 30 - (i_line * 12)
                if line_y < (y - item["height"] + 12): break
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
    text_width, style = PAGE_WIDTH - 40 * mm, ParagraphStyle(
        name="JustifySmall",
        fontName="Times-Roman",
        fontSize=11.5,
        leading=14,
        alignment=TA_JUSTIFY,
        leftIndent=20,
        firstLineIndent=-20,
        spaceAfter=8,
        underlineWidth=0.4,
        underlineOffset= -2.5)
    p = Paragraph(disclaimer_text.replace('\n', ' ').replace('  ', ' '), style)
    w, h = p.wrapOn(c, text_width, PAGE_HEIGHT)
    p.drawOn(c, 20*mm, PAGE_HEIGHT - 170 - h)
    draw_footer(c, page_num)
    c.showPage()
    
# =======================================================
# === FUNGSI UTAMA GENERATE LAPORAN ===
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
    print("\n--- Memulai Pembuatan Laporan Pendek ---")
    try:
        with open("bank_data.txt", "r", encoding="utf-8") as f:
            bank_data_content = f.read()
        print("File 'bank_data.txt' untuk laporan pendek berhasil dimuat.")
    except FileNotFoundError:
        print("Error: file 'bank_data.txt' tidak ditemukan! Konteks AI akan kosong.")
        bank_data_content = ""
    
    ai_analysis_data = generate_short_report_analysis(
        tipe_kepribadian=tipe_kepribadian, kognitif_utama=kognitif_utama_key,
        pekerjaan=pekerjaan, model_ai=model_ai, bank_data_text=bank_data_content
    )
    job_fit_data = generate_job_fit_data(
        full_job_fit_html_text=person_job_fit_text_from_long_report, model_ai=model_ai
    )

    personality_data_for_pdf = {
        "trait_1_title": personality_title,
        "trait_1_desc": personality_desc,
        "trait_2_title": cognitive_title,
        "trait_2_desc": cognitive_desc,
    }
    personality_data_for_pdf.update(ai_analysis_data)
    
    disclaimer_text = 'Profiling ini <b>bukan merupakan tes psikologi</b> melainkan <b>deskripsi profile respon elektrofisiologis sistem syaraf terhadap stimulus behavioral traits dan cognitive traits</b> yang dihitung melalui brain power EEG Emotive system yaitu skor EEG brain power enggagement, excitemen dan interest. Profiling ini menggunakan sumber bukti validitas dari penelitian sebelumnya. EEG dapat digunakan secara efektif untuk memprediksi kepribadian dengan akurasi yang tinggi. Zhu et al. (2002) melaporkan prediksi EEG trait agreeableness dengan akurasi hingga 86%. <u><font color="#3366cc">Zhu et al., 2020</font></u>. <u><font color="#3366cc">Liu et al., 2022</font></u> menunjukkan bahwa model berbasis EEG dapat mencapai akurasi 92.2% dalam memprediksi trait openness <u><font color="#3366cc">Liu et al., 2022</font></u>. <u><font color="#3366cc">Rana et al., 2021</font></u> menemukan bahwa analisis emosi dari sinyal EEG memprediksi extraversion dengan akurasi 81.08% dan agreeableness dengan 86.11% <u><font color="#3366cc">Rana et al., 2021</font></u>.'

    c = canvas.Canvas(nama_file_output, pagesize=A4)
    halaman_1_cover(c, biodata_kandidat, topoplot_path_behaviour, topoplot_path_cognitive, tipe_kepribadian, kognitif_utama_key, page_num=1)
    halaman_2_traits(c, personality_data_for_pdf, page_num=2)
    halaman_3_job_fit(c, job_fit_data, page_num=3)
    halaman_4_disclaimer(c, disclaimer_text, page_num=4)
    c.save()
    print(f"PDF Laporan Pendek '{nama_file_output}' berhasil dibuat!")