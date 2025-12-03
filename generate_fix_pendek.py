# filename: generate_fix_pendek.py (Versi Final - Layout Halaman 2 Vertikal Lebar)

from typing import Optional
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color, black, white, HexColor
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase.pdfmetrics import stringWidth

import requests
import re
import os

PAGE_WIDTH, PAGE_HEIGHT = A4
FOOTER_MARGIN = 40 * mm

class OllamaConnectionError(Exception):
    """Exception khusus untuk menandai error koneksi ke Ollama."""
    pass

# ==============================================================================
# === FUNGSI BANTUAN & AI ===
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
            json={ "model": model, "prompt": prompt, "stream": False, "options": { "temperature": 0.2, "top_p": 0.9, "num_predict": 2048, "repeat_penalty": 1.2 } },
            timeout=600
        )
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "").strip()
            if not generated_text: return f"Error: Model tidak menghasilkan response."
            print(f"   -- Berhasil meng-generate '{task_name}'.")
            return generated_text
        raise OllamaConnectionError(f"Error: HTTP {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        raise OllamaConnectionError("Tidak bisa terhubung ke Ollama server. Pastikan 'ollama serve' sudah berjalan.")
    except Exception as e:
        raise OllamaConnectionError(f"Error saat generate {task_name}: {str(e)}")

def extract_relevant_data(full_text, keywords):
    all_headings = ["Openess", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism", "Kraepelin Test (Numerik)", "WCST (Logika)", "Digit Span (Short Term Memory)"]
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

def generate_short_report_analysis(tipe_kepribadian, kognitif_utama, pekerjaan, model_ai, bank_data_text, suitability_level: Optional[str] = None, average_score: Optional[float] = None):
    print("\nMemulai analisis AI (Metode Dynamic Master Analysis)...")
    specific_context = extract_relevant_data(bank_data_text, [tipe_kepribadian, kognitif_utama])
    prompt_suggestions_final = """
        Berdasarkan analisis profil berikut, berikan 4 rekomendasi pengembangan diri.
        ANALISIS: "{master_analysis}"
        TUGAS: Tulis 4 rekomendasi pengembangan yang **singkat dan memberikan contoh nyata**.
        INSTRUKSI WAJIB:
        1.  Tulis dalam format daftar (4 poin).
        2.  Setiap poin harus berupa kalimat perintah yang actionable.
        3.  Berikan **contoh aktivitas spesifik** di setiap poin.
        4.  Panjang setiap poin **sekitar 15-25 kata** agar jelas.
        5.  **MUTLAK: Jangan menulis kalimat pembuka**. Langsung mulai dengan poin pertama.
    """
    def clean_ai_list(text_list):
        return [line for line in text_list if not any(line.lower().strip().startswith(starter) for starter in ["berikut adalah", "inilah", "ini adalah", "berikut ini"])]
    if not pekerjaan or not pekerjaan.strip():
        return {"suitability": "Pertimbangan Berdasarkan Brain Wave Analysis", "position": "Analisis Profil Psikologis Umum", "reasons_title": "Pertimbangan:", "reasons": [], "suggestions": [], "tips": "Analisis umum."}
    else:
        prompt_master = f"Anda adalah seorang analis psikologi.\nTUGAS: Tulis analisis mendalam (2-3 paragraf) tentang profil kandidat untuk posisi yang ditentukan.\nPROFIL: Kepribadian {tipe_kepribadian}, Kognitif {kognitif_utama}.\nPOSISI: {pekerjaan}.\nKONTEKS DATA:\n---\n{specific_context}\n---"
        master_analysis = generate_ai_content(prompt_master, model=model_ai, task_name="Langkah 1: Master Analysis (Pekerjaan)")
        determined_level = suitability_level or "SESUAI DENGAN CATATAN PENGEMBANGAN"
        prompt_reasons = f'Berdasarkan teks analisis berikut, individu dinilai \'{determined_level}\' untuk pekerjaan tersebut.\nANALISIS: "{master_analysis}"\nTUGAS: Identifikasi 4 alasan utama berupa kekuatan atau sifat positif.\nINSTRUKSI:\n1. Tulis dalam format daftar singkat (4 poin).\n2. Setiap poin ringkas, maksimal 8 kata.\n3. Jangan sertakan kalimat pembuka/penutup.'
        reasons_text = generate_ai_content(prompt_reasons, model=model_ai, task_name="Langkah 3: Ekstrak Alasan")
        suggestions_text = generate_ai_content(prompt_suggestions_final.format(master_analysis=master_analysis), model=model_ai, task_name="Langkah 4: Ekstrak Saran")
        prompt_tips = f"Berdasarkan analisis mendalam berikut, berikan satu saran praktis atau \"tips pamungkas\" untuk sukses dalam pekerjaannya.\nANALISIS: \"{master_analysis}\"\nTUGAS: Tuliskan dalam satu kalimat inspiratif, maksimal 20 kata."
        tips_text = generate_ai_content(prompt_tips, model=model_ai, task_name="Langkah 5: Ekstrak Kesimpulan")
        reasons_cleaned = [re.sub(r'^[-\*\d\.\s\\]+', '', line).strip() for line in reasons_text.split('\n') if line.strip()]
        suggestions_cleaned = [re.sub(r'^[-\*\d\.\s\\]+', '', line).strip() for line in suggestions_text.split('\n') if line.strip()]
        final_suitability_text = determined_level
        if determined_level and average_score is not None:
            try:
                final_suitability_text = f"{determined_level} ({average_score:.0f}%)"
            except (ValueError, TypeError): pass
        return {"suitability": final_suitability_text, "position": pekerjaan, "reasons_title": "Pertimbangan :", "reasons": clean_ai_list(reasons_cleaned), "suggestions": clean_ai_list(suggestions_cleaned), "tips": tips_text.strip()}

def generate_job_fit_data(full_job_fit_html_text, model_ai):
    print("\nMemulai peringkasan AI untuk Rekomendasi Pekerjaan...")
    if not full_job_fit_html_text or "Error:" in full_job_fit_html_text: return [{"title": "Analisis Gagal", "reason": "Data sumber tidak tersedia."}] * 6
    plain_text = re.sub('<[^<]+?>', '', full_job_fit_html_text)
    prompt_summarize_jobs = f"Anda AI ahli meringkas informasi.\nTUGAS: Dari teks di bawah, identifikasi 6 judul pekerjaan dan penjelasannya. Tulis ulang penjelasannya menjadi alasan singkat (maksimal 15 kata).\nTEKS SUMBER:\n---\n{plain_text}\n---\nFORMAT OUTPUT WAJIB:\n[Nama Pekerjaan 1]: [Alasan singkat]\n[Nama Pekerjaan 2]: [Alasan singkat]\n...\n(Harus 6 baris)"
    raw_text = generate_ai_content(prompt_summarize_jobs, model=model_ai, task_name="Peringkasan Rekomendasi Pekerjaan")
    if "Error:" in raw_text: return [{"title": "Analisis Gagal", "reason": raw_text}] * 6
    recommendations = []
    for line in raw_text.strip().split('\n'):
        if ':' in line:
            parts = line.split(':', 1); title, reason = parts[0].strip().lstrip('*- '), parts[1].strip()
            if title and reason: recommendations.append({"title": title, "reason": reason})
    return recommendations[:6]

def draw_watermark(c, watermark_path):
    try:
        img = ImageReader(watermark_path); iw, ih = img.getSize(); w_target, h_target = 130 * mm, (130 * mm) * ih / iw
        x, y = (PAGE_WIDTH - w_target) / 2, (PAGE_HEIGHT - h_target) / 2
        c.saveState(); c.drawImage(img, x, y, width=w_target, height=h_target, mask='auto'); c.restoreState()
    except Exception as e: print(f"⚠️ Watermark gagal dimuat: {e}")

def draw_header(c, logo_path="cia.png"):
    try:
        img = ImageReader(logo_path); iw, ih = img.getSize(); w_target, h_target = 50 * mm, (50 * mm) * ih / iw
        x, y = 20 * mm, PAGE_HEIGHT - h_target - 10 * mm
        c.drawImage(img, x, y, width=w_target, height=h_target, mask='auto')
    except Exception as e: print(f"Logo gagal dimuat: {e}")
    c.setFont("Times-Bold", 14); c.drawRightString(PAGE_WIDTH - 25 * mm, PAGE_HEIGHT - 20 * mm, "CENTRAL IMPROVEMENT ACADEMY")
    c.setFont("Times-Roman", 12); c.drawRightString(PAGE_WIDTH - 25 * mm, PAGE_HEIGHT - 25 * mm, "Jl. Balikpapan No.27, RT.9/RW.6, Petojo Sel.,")
    c.drawRightString(PAGE_WIDTH - 25 * mm, PAGE_HEIGHT - 30 * mm, "Kecamatan Gambir, Jakarta Pusat"); c.drawRightString(PAGE_WIDTH - 25 * mm, PAGE_HEIGHT - 35 * mm, "0811-3478-000")
    c.setLineWidth(4); c.setStrokeColor(black); garis_y = PAGE_HEIGHT - 42 * mm; c.line(25 * mm, garis_y, PAGE_WIDTH - 25 * mm, garis_y)

def draw_footer(c, page_num):
    c.setFont("Times-Roman", 12); c.setFillColor(black); c.drawRightString(PAGE_WIDTH - 10 * mm, 10 * mm, f"{page_num}")

def draw_centered_image(c, img_path, y_top, width_mm):
    try:
        image = ImageReader(img_path); iw, ih = image.getSize(); width, height = width_mm * mm, (width_mm * mm) * ih / iw
        x, y = (PAGE_WIDTH - width) / 2, y_top - height
        c.drawImage(img_path, x, y, width=width, height=height, mask='auto')
        return y, height
    except Exception as e:
        print(f"Gambar '{img_path}' tidak ditemukan atau error: {e}")
        return y_top - 100, 100

def wrap_text_to_width(text, font_name, font_size, max_width_mm):
    if not text or not text.strip(): return [""]
    max_width_points, words, lines, current_line = max_width_mm * mm, text.split(), [], ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if stringWidth(test_line, font_name, font_size) <= max_width_points: current_line = test_line
        else:
            if current_line: lines.append(current_line)
            current_line = word
    if current_line: lines.append(current_line)
    return lines if lines else [""]

def halaman_1_baru(c, biodata, table_data, ai_data, personality_name, cognitive_name, job_name, page_num):
    draw_watermark(c, "cia_watermark.png"); draw_header(c)
    
    # Mengatur ulang posisi awal sedikit lebih tinggi untuk menghemat ruang
    c.setFont("Times-Bold", 18); c.setFillColorRGB(0, 0.2, 0.6); c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 145, "BRAIN WAVE PROFILING")
    c.setFillColor(black); c.setFont("Times-Roman", 12); y = PAGE_HEIGHT - 160
    for label, value in biodata.items():
        c.drawString(60, y, f"{label}"); c.drawString(180, y, f": {value}"); y -= 16
    
    if table_data:
        # Mengurangi spasi sebelum dan sesudah tabel
        y -= 15; c.setFont("Times-Bold", 12); c.drawString(60, y, f"ANALISIS KECOCOKAN UNTUK: {job_name.upper()}"); y -= 10
        cell_style = ParagraphStyle("TableCell", fontSize=9, leading=11, wordWrap="CJK")
        headers = [Paragraph("Kompetensi Utama", cell_style), Paragraph(f"{personality_name} (%)", cell_style), Paragraph(f"{cognitive_name} (%)", cell_style), Paragraph("Rata-rata (%)", cell_style), Paragraph("Interpretasi", cell_style)]
        data_for_table = [headers] + [[Paragraph(str(cell), cell_style) for cell in row] for row in table_data]
        table = Table(data_for_table, colWidths=[5.5*cm, 2.5*cm, 3*cm, 2.5*cm, 3*cm])
        table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.lightblue), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('ALIGN', (1,1), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('FONTNAME', (0,0), (-1,0), 'Times-Bold'), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke)]))
        w, h = table.wrapOn(c, PAGE_WIDTH - 120, y); table.drawOn(c, 60, y - h); y -= (h + 15)

    style_alasan = ParagraphStyle(name='alasan', fontName='Times-Roman', fontSize=10, leading=14)
    total_reasons_height = sum(Paragraph(f"{i+1}. {markdown_to_html_platypus(reason_md)}", style_alasan).wrapOn(c, 150*mm, 20*mm)[1] + 4 for i, reason_md in enumerate(ai_data.get('reasons', [])))
    # Mengurangi padding vertikal di dalam kotak Pertimbangan
    suitability_height = total_reasons_height + 35*mm 
    
    if y - suitability_height < FOOTER_MARGIN:
        draw_footer(c, page_num); c.showPage(); page_num += 1
        draw_watermark(c, "cia_watermark.png"); draw_header(c); y = PAGE_HEIGHT - 60 * mm

    kuning_muda_border = HexColor("#D4C299")
    c.setFillColorRGB(255/255, 242/255, 204/255, alpha=0.85); c.setStrokeColor(kuning_muda_border); c.setLineWidth(1.5)
    c.roundRect(25*mm, y - suitability_height, 160*mm, suitability_height, 5*mm, fill=1, stroke=1)
    c.setFillColor(black); c.setFont("Times-Bold", 12); c.drawCentredString(105*mm, y - 20, f"■ {ai_data.get('suitability', '')}")
    c.drawCentredString(105*mm, y - 35, ai_data.get("position", '')); c.setFont("Times-Bold", 12); c.drawString(35*mm, y - 50, ai_data.get("reasons_title", ''))
    y_alasan = y - 65
    for i, reason_md in enumerate(ai_data.get('reasons', [])):
        p = Paragraph(f"{i+1}. {markdown_to_html_platypus(reason_md)}", style_alasan)
        w, h = p.wrapOn(c, 150*mm, 20*mm); p.drawOn(c, 30*mm, y_alasan-h); y_alasan -= (h + 4)

    draw_footer(c, page_num); c.showPage()
    return page_num + 1

def halaman_2_baru(c, topoplot_behavior, topoplot_cognitive, tipe_kepribadian, kognitif_nama, biodata, data_traits, page_num):
    draw_watermark(c, "cia_watermark.png"); draw_header(c)

    y_pos = PAGE_HEIGHT - 55*mm
    nama_kandidat = biodata.get("Nama", "Kandidat")

    # --- Helper function untuk menggambar satu blok (Gambar + Kotak Penjelasan Lebar) ---
    def draw_block(y_start, img_path, caption, box_label, trait_title, trait_desc):
        # 1. Gambar Topoplot
        y_after_img, img_height = draw_centered_image(c, img_path, y_start, 150)
        c.setFont("Times-Bold", 10)
        c.drawCentredString(PAGE_WIDTH / 2, y_after_img - 10, caption)
        
        y_current = y_after_img - 20 * mm

        # 2. Gambar Kotak Deskripsi Lebar
        biru_vibrant, kuning_gold = HexColor("#1E88E5"), HexColor("#FCD116")
        biru_border, kuning_border = HexColor("#1565C0"), HexColor("#D4A914")
        box_width = 160 * mm
        start_x = (PAGE_WIDTH - box_width) / 2

        p_temp = Paragraph(trait_desc, ParagraphStyle(name='temp', textColor=white, fontName='Times-Roman', fontSize=10, leading=12, alignment=TA_CENTER))
        w, h = p_temp.wrapOn(c, box_width - 20, 100*mm)
        box_height = h + 30 * mm # Padding lebih sedikit karena lebih lebar

        c.setFillColor(biru_vibrant); c.setStrokeColor(biru_border); c.setLineWidth(1.5)
        c.roundRect(start_x, y_current - box_height, box_width, box_height, 5*mm, fill=1, stroke=1)
        
        label_width, label_height = 70, 20
        label_x = start_x + (box_width - label_width) / 2
        label_y = y_current + 5
        c.setFillColor(kuning_gold); c.setStrokeColor(kuning_border); c.setLineWidth(1)
        c.rect(label_x, label_y - label_height / 2, label_width, label_height, fill=1, stroke=1)
        c.setFillColor(black); c.setFont("Times-Bold", 12)
        c.drawCentredString(label_x + label_width / 2, label_y - 4, box_label)

        c.setFillColor(white); c.setFont("Times-Bold", 12)
        c.drawCentredString(start_x + box_width/2, y_current - 20, f"✓ {trait_title}")
        
        p = Paragraph(trait_desc, p_temp.style)
        p.wrapOn(c, box_width - 20, box_height - 30)
        p.drawOn(c, start_x + 10, y_current - 25 - p.height)
        
        return y_current - box_height

    # --- Menggambar Blok 1 (Gambar + Kotak Penjelasan) ---
    caption1 = f"Gambar 1. Topografi respons {nama_kandidat} terhadap stimulus behavioral trait {tipe_kepribadian.lower()}"
    y_pos = draw_block(y_pos, topoplot_behavior, caption1, "Gambar 1", data_traits['trait_1_title'], data_traits['trait_1_desc'])
    
    # --- Menggambar Blok 2 (Gambar + Kotak Penjelasan) ---
    y_pos -= 10 * mm # Spasi antar blok
    caption2 = f"Gambar 2. Brain topografi Brain Wave Analysis Power stimulus {kognitif_nama.split('(')[0].strip().lower()}"
    draw_block(y_pos, topoplot_cognitive, caption2, "Gambar 2", data_traits['trait_2_title'], data_traits['trait_2_desc'])

    draw_footer(c, page_num); c.showPage()
    return page_num + 1

def halaman_3_baru(c, ai_data, page_num):
    draw_watermark(c, "cia_watermark.png"); draw_header(c)
    y_pos = PAGE_HEIGHT - 60*mm; margin_v = 10 * mm
    merah_muda_border = HexColor("#D4BBA3"); style_saran = ParagraphStyle(name='saran', fontName='Times-Roman', fontSize=11, leading=14)
    total_text_height = 0; paragraphs = []
    for suggestion_md in ai_data.get('suggestions', []):
        p = Paragraph(f"• {markdown_to_html_platypus(suggestion_md)}", style_saran)
        w, h = p.wrapOn(c, 150*mm, 100*mm); total_text_height += h + (2*mm); paragraphs.append(p)
    padding_v = 35 * mm; pengembangan_height = total_text_height + padding_v
    c.setFillColorRGB(252/255, 228/255, 214/255, alpha=0.85); c.setStrokeColor(merah_muda_border); c.setLineWidth(1.5)
    c.roundRect(25*mm, y_pos - pengembangan_height, 160*mm, pengembangan_height, 5*mm, fill=1, stroke=1)
    c.setFillColor(black); c.setFont("Times-Bold", 13); c.drawCentredString(105*mm, y_pos - 20, "Area Pengembangan yang Dapat Dilakukan")
    y_saran = y_pos - 30
    for p in paragraphs:
        p.drawOn(c, 30*mm, y_saran - p.height); y_saran -= p.height + (2*mm)
    y_pos -= (pengembangan_height + margin_v)
    biru_vibrant, biru_border = HexColor("#1E88E5"), HexColor("#1565C0")
    style_tips = ParagraphStyle(name='tips', fontName='Times-Roman', fontSize=11, leading=14, alignment=TA_CENTER, textColor=white)
    p_tips = Paragraph(f'{markdown_to_html_platypus(ai_data.get("tips", ""))}', style_tips)
    w_tips, h_tips = p_tips.wrapOn(c, 150*mm, 30*mm); tips_height = h_tips + (15*mm)
    c.setFillColor(biru_vibrant); c.setStrokeColor(biru_border); c.setLineWidth(1.5)
    c.roundRect(25*mm, y_pos - tips_height, 160*mm, tips_height, 5*mm, fill=1, stroke=1)
    p_tips.drawOn(c, (PAGE_WIDTH-w_tips)/2, y_pos - (tips_height + h_tips)/2 + (5*mm))
    draw_footer(c, page_num); c.showPage()
    return page_num + 1

def halaman_4_baru_job_fit(c, job_data, page_num):
    draw_watermark(c, "cia_watermark.png"); draw_header(c)
    c.setFont("Times-Bold", 14); c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 150, "PERSON TO FIT BIDANG KERJA/USAHA")
    valid_job_data = [job for job in job_data if "Data Tidak Tersedia" not in job.get("title", "")]
    box_width, h_gap, v_gap = 88 * mm, 10 * mm, 10 * mm
    x_start, y_start = (PAGE_WIDTH - (2*box_width + h_gap))/2, PAGE_HEIGHT - 170
    box_data = []
    for job in valid_job_data: 
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
            c.saveState(); c.setFillColor(Color(0.88, 0.94, 0.85, alpha=0.8)); c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(x, y - item["height"], box_width, item["height"], fill=1, stroke=1); c.restoreState()
            text_x, text_y = x + 10, y - 20
            c.setFont("Times-Bold", 12); c.setFillColor(black); c.drawString(text_x, text_y, f"{item['job']['title']}")
            c.setFont("Times-Bold", 11); c.drawString(text_x, text_y - 15, "Pertimbangan:")
            c.setFont("Times-Roman", 11)
            for i_line, line in enumerate(item["wrapped"]):
                line_y = text_y - 30 - (i_line * 12)
                if line_y < (y - item["height"] + 12): break
                c.drawString(text_x, line_y, line)
        y_cursor -= max_row_height + v_gap
    draw_footer(c, page_num); c.showPage()
    return page_num + 1

def halaman_5_baru_disclaimer(c, disclaimer_text, page_num):
    draw_watermark(c, "cia_watermark.png"); draw_header(c)
    c.setFont("Times-Bold", 12); c.setFillColor(black); c.drawString(20 * mm, PAGE_HEIGHT - 150, "Disclaimer")
    text_width, style = PAGE_WIDTH - 40 * mm, ParagraphStyle(name="JustifySmall", fontName="Times-Roman", fontSize=11.5, leading=14, alignment=TA_JUSTIFY, underlineWidth=0.4, underlineOffset= -2.5)
    clean_text = disclaimer_text.replace('\n', ' ').replace('  ', ' ')
    p = Paragraph(clean_text, style)
    w, h = p.wrapOn(c, text_width, PAGE_HEIGHT); p.drawOn(c, 20*mm, PAGE_HEIGHT - 170 - h)
    draw_footer(c, page_num); c.showPage()
    return page_num + 1

def generate_short_report(
    tipe_kepribadian, kognitif_utama_key, pekerjaan, model_ai,
    nama_file_output, biodata_kandidat, topoplot_path_behaviour,
    topoplot_path_cognitive, personality_title, personality_desc,
    cognitive_title, cognitive_desc, person_job_fit_text_from_long_report: str,
    suitability_level: Optional[str] = None,
    suitability_table_data: Optional[list] = None,
    average_score: Optional[float] = None
):
    print("\n--- Memulai Pembuatan Laporan Pendek dengan Layout Final ---")
    try:
        with open("bank_data.txt", "r", encoding="utf-8") as f: bank_data_content = f.read()
    except FileNotFoundError: bank_data_content = ""
    
    ai_analysis_data = generate_short_report_analysis(tipe_kepribadian=tipe_kepribadian, kognitif_utama=kognitif_utama_key, pekerjaan=pekerjaan, model_ai=model_ai, bank_data_text=bank_data_content, suitability_level=suitability_level, average_score=average_score)
    job_fit_data = generate_job_fit_data(full_job_fit_html_text=person_job_fit_text_from_long_report, model_ai=model_ai)
    data_traits = {"trait_1_title": personality_title, "trait_1_desc": personality_desc, "trait_2_title": cognitive_title, "trait_2_desc": cognitive_desc}
    disclaimer_text = 'Profiling ini <b>bukan merupakan tes psikologi</b> melainkan <b>deskripsi profile respon elektrofisiologis sistem syaraf terhadap stimulus behavioral traits dan cognitive traits</b> yang dihitung melalui brain power EEG Emotive system yaitu skor EEG brain power enggagement, excitemen dan interest. Profiling ini menggunakan sumber bukti validitas dari penelitian sebelumnya. EEG dapat digunakan secara efektif untuk memprediksi kepribadian dengan akurasi yang tinggi. Zhu et al. (2002) melaporkan prediksi EEG trait agreeableness dengan akurasi hingga 86%. <u><font color="#3366cc">Zhu et al., 2020</font></u>. <u><font color="#3366cc">Liu et al., 2022</font></u> menunjukkan bahwa model berbasis EEG dapat mencapai akurasi 92.2% dalam memprediksi trait openness <u><font color="#3366cc">Liu et al., 2022</font></u>. <u><font color="#3366cc">Rana et al., 2021</font></u> menemukan bahwa analisis emosi dari sinyal EEG memprediksi extraversion dengan akurasi 81.08% dan agreeableness dengan 86.11% <u><font color="#3366cc">Rana et al., 2021</font></u>.'

    c = canvas.Canvas(nama_file_output, pagesize=A4)
    next_page_num = 1
    next_page_num = halaman_1_baru(c, biodata_kandidat, suitability_table_data, ai_analysis_data, tipe_kepribadian, kognitif_utama_key, pekerjaan, page_num=next_page_num)
    next_page_num = halaman_2_baru(c, topoplot_path_behaviour, topoplot_path_cognitive, tipe_kepribadian, kognitif_utama_key, biodata_kandidat, data_traits, page_num=next_page_num)
    next_page_num = halaman_3_baru(c, ai_analysis_data, page_num=next_page_num)
    next_page_num = halaman_4_baru_job_fit(c, job_fit_data, page_num=next_page_num)
    next_page_num = halaman_5_baru_disclaimer(c, disclaimer_text, page_num=next_page_num)

    c.save()
    print(f"PDF Laporan Pendek '{nama_file_output}' berhasil dibuat dengan layout final!")