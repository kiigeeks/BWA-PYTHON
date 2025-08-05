from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color, black, white, HexColor
from textwrap import wrap
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfbase.pdfmetrics import stringWidth

PAGE_WIDTH, PAGE_HEIGHT = A4

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

    # --- Teks Alamat dan Judul ---
    c.setFont("Times-Bold", 14)
    c.drawRightString(PAGE_WIDTH - 25 * mm, PAGE_HEIGHT - 20 * mm, "CENTRAL IMPROVEMENT ACADEMY")

    c.setFont("Times-Roman", 12)
    c.drawRightString(PAGE_WIDTH - 25 * mm, PAGE_HEIGHT - 25 * mm, "Jl. Balikpapan No.27, RT.9/RW.6, Petojo Sel.,")
    c.drawRightString(PAGE_WIDTH - 25 * mm, PAGE_HEIGHT - 30 * mm, "Kecamatan Gambir, Jakarta Pusat")
    c.drawRightString(PAGE_WIDTH - 25 * mm, PAGE_HEIGHT - 35 * mm, "0811-3478-000")

    # --- Garis Horizontal Hitam Tebal ---
    if not is_cover:
        c.setLineWidth(4)
        c.setStrokeColor(black)
        garis_y = PAGE_HEIGHT - 42 * mm
        c.line(25 * mm, garis_y, PAGE_WIDTH - 25 * mm, garis_y)

def draw_footer(c, page_num):
    c.setFont("Times-Roman", 12)
    c.setFillColor(black)  # Pastikan warna hitam
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
    except:
        print(f"Gambar '{img_path}' tidak ditemukan.")
        return y_top - 100

def wrap_text_to_width(text, font_name, font_size, max_width_mm):
    """
    Membungkus teks berdasarkan lebar maksimum dalam mm.
    Return list of strings yang sudah dibungkus.
    """
    if not text or not text.strip():
        return [""]
    
    # Konversi mm ke points
    max_width_points = max_width_mm * mm
    
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        # Test apakah menambahkan kata ini masih muat dalam satu baris
        if current_line:
            test_line = current_line + " " + word
        else:
            test_line = word
            
        # Ukur lebar test_line dalam points
        test_width = stringWidth(test_line, font_name, font_size)
        
        if test_width <= max_width_points:
            # Masih muat, tambahkan ke current_line
            current_line = test_line
        else:
            # Tidak muat, simpan current_line dan mulai baris baru
            if current_line:
                lines.append(current_line)
            
            # Cek apakah kata tunggal terlalu panjang
            word_width = stringWidth(word, font_name, font_size)
            if word_width > max_width_points:
                # Pecah kata per karakter
                char_line = ""
                for char in word:
                    test_char = char_line + char
                    if stringWidth(test_char, font_name, font_size) <= max_width_points:
                        char_line = test_char
                    else:
                        if char_line:
                            lines.append(char_line)
                        char_line = char
                current_line = char_line
            else:
                current_line = word
    
    # Tambahkan baris terakhir
    if current_line:
        lines.append(current_line)
    
    return lines if lines else [""]

def halaman_1_cover(c, biodata, topoplot1, topoplot2, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    # === Judul Tengah ===
    c.setFont("Times-Bold", 18)
    c.setFillColorRGB(0, 0.2, 0.6)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 150, "BRAIN WAVE PROFILING")
    c.setFillColor(black)

    # === Biodata ===
    c.setFont("Times-Roman", 12)
    y = PAGE_HEIGHT - 170
    for label, value in biodata.items():
        c.drawString(60, y, f"{label}")
        c.drawString(180, y, f": {value}")
        y -= 16

    # === EXECUTIVE SUMMARY ===
    c.setFont("Times-Bold", 12)
    c.drawString(60, y - 15, "EXECUTIVE SUMMARY")

    # === Topoplot 1 ===
    y = draw_centered_image(c, topoplot1, y - 40, 150)
    c.setFont("Times-Bold", 11)
    nama = biodata.get("Nama", "")
    c.drawCentredString(PAGE_WIDTH / 2, y - 10, f"Gambar 1. Topografi response {nama} terhadap stimulus behavioral trait neuroticm")

    # === Topoplot 2 ===
    y = draw_centered_image(c, topoplot2, y - 40, 150)
    c.drawCentredString(PAGE_WIDTH / 2, y - 10, "Gambar 2. Brain topografi Brain Wave Analysis Power stimulus logika")

    # === Footer ===
    draw_footer(c, page_num)
    c.showPage()
def halaman_2_traits(c, data, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    # ===============================
    # Set Warna
    # ===============================
    biru_soft = HexColor("#4F81BD")
    kuning_gold = HexColor("#FCD116")
    kuning_muda = HexColor("#FFF2CC")
    merah_muda = HexColor("#FCE4D6")

    # ===============================
    # Gambar 1 dan 2 Box - DINAMIS MEMANJANG KE BAWAH
    # ===============================
    box_width = 70 * mm
    min_box_height = 40 * mm
    box_gap = 15 * mm
    start_x = (210 * mm - (2 * box_width + box_gap)) / 2
    start_y = 250 * mm
    
    padding_top = 30  # Ruang untuk label + judul
    padding_bottom = 8
    line_height = 12
    
    # PERBAIKAN: Hitung lebar available dengan benar (dalam mm)
    available_width_mm = (box_width / mm) - 10  # 70mm - 10mm padding = 60mm

    # ===============================
    # HITUNG TINGGI BOX DINAMIS
    # ===============================
    # PERBAIKAN: Gunakan font size yang konsisten (11 untuk keduanya)
    font_size = 11
    
    # Box 1
    wrapped_text1 = wrap_text_to_width(data['trait_1_desc'], "Times-Roman", font_size, available_width_mm)
    content_height1_points = padding_top + (len(wrapped_text1) * line_height) + padding_bottom
    box1_height = max(min_box_height, content_height1_points)
    
    # Box 2
    wrapped_text2 = wrap_text_to_width(data['trait_2_desc'], "Times-Roman", font_size, available_width_mm)
    content_height2_points = padding_top + (len(wrapped_text2) * line_height) + padding_bottom
    box2_height = max(min_box_height, content_height2_points)
    
    c.setFillColor(biru_soft)
    c.roundRect(start_x, start_y - box1_height, box_width, box1_height, 5 * mm, fill=1)

    # Label Gambar 1 - Dipusatkan secara horizontal
    label_width = 60
    label_height = 15
    label_text = "Gambar 1"

    label_x = start_x + (box_width - label_width) / 2
    label_y = start_y - label_height  # dari atas box turun 15 pt

    # Gambar kotak kuning
    c.setFillColor(kuning_gold)
    c.rect(label_x, label_y, label_width, label_height, fill=1)

    # Gambar teks di tengah label
    c.setFillColor(black)
    c.setFont("Times-Bold", 11)
    text_width = c.stringWidth(label_text, "Times-Bold", 11)
    text_x = label_x + (label_width - text_width) / 2
    text_y = label_y + 4  # Secara visual agak ke tengah vertikal

    c.drawString(text_x, text_y, label_text)


    # Text Gambar 1
    c.setFillColor(white)
    c.setFont("Times-Bold", 11)
    c.drawString(start_x + 5, start_y - 28, f"✓ {data['trait_1_title']}")
    
    # Render teks dengan batas box1 yang sesuai
    y = start_y - 42
    c.setFont("Times-Roman", font_size)
    box1_bottom = start_y - box1_height + padding_bottom
    
    for line in wrapped_text1:
        if y >= box1_bottom:
            c.drawString(start_x + 5, y, line)
            y -= line_height
        else:
            break

    # ===============================
    # GAMBAR BOX 2 - Tinggi sesuai konten (independen)
    # ===============================
    x2 = start_x + box_width + box_gap
    c.setFillColor(biru_soft)
    c.roundRect(x2, start_y - box2_height, box_width, box2_height, 5 * mm, fill=1)

    # Label Gambar 2 - Dipusatkan secara horizontal
    label_text = "Gambar 2"
    label_x2 = x2 + (box_width - label_width) / 2
    label_y2 = start_y - label_height

    c.setFillColor(kuning_gold)
    c.rect(label_x2, label_y2, label_width, label_height, fill=1)

    c.setFillColor(black)
    c.setFont("Times-Bold", 11)
    text_width2 = c.stringWidth(label_text, "Times-Bold", 11)
    text_x2 = label_x2 + (label_width - text_width2) / 2
    text_y2 = label_y2 + 4

    c.drawString(text_x2, text_y2, label_text)


    # Text Gambar 2
    c.setFillColor(white)
    c.setFont("Times-Bold", 11)
    c.drawString(x2 + 5, start_y - 28, f"✓ {data['trait_2_title']}")
    
    # Render teks dengan batas box2 yang sesuai
    y = start_y - 42
    c.setFont("Times-Roman", font_size)
    box2_bottom = start_y - box2_height + padding_bottom
    
    for line in wrapped_text2:
        if y >= box2_bottom:
            c.drawString(x2 + 5, y, line)
            y -= line_height
        else:
            break

    # ===============================
    # Box Tengah (Suitability) - POSISI BERDASARKAN BOX TERPANJANG
    # ===============================
    # Gunakan box yang paling panjang sebagai referensi untuk elemen selanjutnya
    max_box_height = max(box1_height, box2_height)
    suitability_y_top = start_y - max_box_height - 25
    suitability_width_mm = 150  # dalam mm
    
    # HITUNG TINGGI SUITABILITY BOX BERDASARKAN KONTEN
    suitability_content_lines = 4  # Judul + posisi + spacing
    for reason in data['reasons']:
        wrapped_reason = wrap_text_to_width(reason, "Times-Roman", 10, suitability_width_mm)
        suitability_content_lines += len(wrapped_reason)
    
    suitability_height = max(42 * mm, suitability_content_lines * 3.5 * mm + 20 * mm)
    
    c.setFillColor(kuning_muda)
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.roundRect(25 * mm, suitability_y_top - suitability_height, 160 * mm, suitability_height, 5 * mm, fill=1, stroke=1)
    c.setFillColor(black)
    c.setFont("Times-Bold", 12)
    c.drawCentredString(105 * mm, suitability_y_top - 12, f"{data['suitability']} untuk posisi")
    c.drawCentredString(105 * mm, suitability_y_top - 26, data["position"])

    c.setFont("Times-Roman", 10)
    y = suitability_y_top - 36
    suitability_bottom = suitability_y_top - suitability_height + 5
    
    for i, reason in enumerate(data['reasons']):
        wrapped_reason = wrap_text_to_width(reason, "Times-Roman", 11, suitability_width_mm)
        for line_idx, line in enumerate(wrapped_reason):
            if y >= suitability_bottom:  # PERBAIKAN: Gunakan >= 
                if line_idx == 0:
                    c.drawString(30 * mm, y, f"{i+1}. {line}")
                else:
                    c.drawString(35 * mm, y, line)
                y -= 9
            else:
                break

    # ===============================
    # Box Pengembangan - TINGGI DINAMIS BERDASARKAN KONTEN
    # ===============================
    pengembangan_y_top = suitability_y_top - suitability_height - 12
    
    # HITUNG TINGGI PENGEMBANGAN BOX BERDASARKAN KONTEN
    pengembangan_content_lines = 2  # Judul + spacing
    for suggestion in data['suggestions']:
        wrapped_suggestion = wrap_text_to_width(suggestion, "Times-Roman", 11, suitability_width_mm)
        pengembangan_content_lines += len(wrapped_suggestion)
    
    pengembangan_height = max(28 * mm, pengembangan_content_lines * 3 * mm + 15 * mm)
    
    c.setFillColor(merah_muda)
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.roundRect(25 * mm, pengembangan_y_top - pengembangan_height, 160 * mm, pengembangan_height, 5 * mm, fill=1, stroke=1)
    c.setFillColor(black)
    c.setFont("Times-Bold", 11)
    c.drawString(30 * mm, pengembangan_y_top - 12, "Pengembangan yang Harus Dilakukan")

    c.setFont("Times-Roman", 11)
    y = pengembangan_y_top - 22
    pengembangan_bottom = pengembangan_y_top - pengembangan_height + 5
    
    for suggestion in data['suggestions']:
        wrapped_suggestion = wrap_text_to_width(suggestion, "Times-Roman", 11, suitability_width_mm)
        for line_idx, line in enumerate(wrapped_suggestion):
            if y >= pengembangan_bottom:  # PERBAIKAN: Gunakan >=
                if line_idx == 0:
                    c.drawString(30 * mm, y, f"- {line}")
                else:
                    c.drawString(35 * mm, y, line)
                y -= 8
            else:
                break

    # ===============================
    # Footer Tips - TINGGI DINAMIS BERDASARKAN KONTEN
    # ===============================
    tips_y_top = pengembangan_y_top - pengembangan_height - 12
    
    # HITUNG TINGGI TIPS BOX BERDASARKAN KONTEN
    wrapped_tips = wrap_text_to_width(data['tips'], "Times-Roman", 11, suitability_width_mm)
    tips_height = max(22 * mm, len(wrapped_tips) * 3 * mm + 10 * mm)
    
    # Safety check: minimal 25mm dari footer
    min_y_from_bottom = 25 * mm
    calculated_bottom = tips_y_top - tips_height
    
    if calculated_bottom < min_y_from_bottom:
        tips_y_top = min_y_from_bottom + tips_height
    
    c.setFillColor(biru_soft)
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.roundRect(25 * mm, tips_y_top - tips_height, 160 * mm, tips_height, 5 * mm, fill=1, stroke=1)
    c.setFillColor(white)
    c.setFont("Times-Roman", 11)
    
    # Center teks secara vertikal dalam box
    total_text_height = len(wrapped_tips) * 8
    start_text_y = tips_y_top - (tips_height / 2) + (total_text_height / 2)
    
    y = start_text_y
    tips_bottom = tips_y_top - tips_height + 3
    
    for line in wrapped_tips:
        if y >= tips_bottom:  # PERBAIKAN: Gunakan >=
            c.drawCentredString(105 * mm, y, f'"{line}"')
            y -= 8
        else:
            break

    # Reset warna dan footer
    c.setFillColor(black)
    draw_footer(c, page_num)
    c.showPage()
    
def halaman_3_job_fit(c, job_data, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    c.setFont("Times-Bold", 14)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 150, "PERSON TO FIT BIDANG KERJA/USAHA")

    # --- Layout dan font ---
    box_width = 88 * mm
    h_gap = 10 * mm
    v_gap = 10 * mm
    total_row_width = (2 * box_width) + h_gap
    x_start = (PAGE_WIDTH - total_row_width) / 2

    y_start = PAGE_HEIGHT - 170

    font_name = "Times-Roman"
    font_size = 11
    line_height = 12

    # --- Padding top/bottom dalam point ---
    padding_top = 20
    padding_bottom = 12
    min_box_height = 45 * mm

    # Lebar teks dalam mm (box width - padding kiri kanan)
    text_width_mm = (box_width - 15) / mm

    # --- Preprocess semua data job: bungkus teks + hitung tinggi kotak ---
    box_data = []
    for job in job_data:
        wrapped = wrap_text_to_width(job['reason'], font_name, font_size, text_width_mm)
        num_lines = len(wrapped)
        content_height_points = padding_top + (num_lines * line_height) + padding_bottom
        dynamic_height = max(min_box_height, content_height_points)  # content_height_points sudah dalam points
        box_data.append({
            "job": job,
            "wrapped": wrapped,
            "height": dynamic_height
        })

    # --- Render 2 kolom per baris dengan Y konsisten ---
    y_cursor = y_start
    for row in range(0, len(box_data), 2):
        row_items = box_data[row:row+2]
        max_row_height = max(item["height"] for item in row_items)

        for col, item in enumerate(row_items):
            x = x_start + col * (box_width + h_gap)
            y = y_cursor

            # --- Draw box ---
            c.saveState()
            c.setFillColor(Color(0.88, 0.94, 0.85, alpha=0.8))
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(x, y - item["height"], box_width, item["height"], fill=1, stroke=1)
            c.restoreState()

            # --- Draw text ---
            text_x = x + 10
            text_y = y - padding_top
            job = item["job"]

            c.setFont("Times-Bold", 12)
            c.setFillColor(black)
            c.drawString(text_x, text_y, f"{job['title']}")

            c.setFont("Times-Bold", 11)
            c.drawString(text_x, text_y - 15, "Alasan:")

            c.setFont(font_name, font_size)
            for i_line, line in enumerate(item["wrapped"]):
                line_y = text_y - 30 - (i_line * line_height)
                # Cegah baris terlalu dekat atau melewati batas bawah box
                if line_y < (y - item["height"] + padding_bottom):
                    break
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

    # Margin untuk area teks
    left_margin = 20 * mm
    right_margin = 20 * mm
    top_margin = PAGE_HEIGHT - 170
    
    # Lebar area yang tersedia untuk teks
    text_width = PAGE_WIDTH - left_margin - right_margin
    
    # Buat style untuk paragraf: rata kiri-kanan (justify)
    style = ParagraphStyle(
        name='Justified',
        fontName='Times-Roman',
        fontSize=10,
        leading=15,
        alignment=TA_JUSTIFY,
        underlineColor=None,
        underlineWidth=0.4,
        underlineOffset=-2.5    
    )
    
    # Ganti spasi biasa dengan spasi yang lebih 'fleksibel' untuk justifikasi yang lebih baik
    text_for_paragraph = disclaimer_text.replace('\n', ' ').replace('  ', ' ')
    
    # Buat objek Paragraf
    p = Paragraph(text_for_paragraph, style)
    
    # Hitung tinggi yang dibutuhkan oleh paragraf dan gambar ke kanvas
    w, h = p.wrapOn(c, text_width, PAGE_HEIGHT)
    p.drawOn(c, left_margin, top_margin - h)

    c.setFont("Times-Bold", 10)
    c.setFillColorRGB(0.6, 0.6, 0.6)

    draw_footer(c, page_num)
    c.showPage()

# ================== MAIN EKSEKUSI =====================
if __name__ == "__main__":
    c = canvas.Canvas("laporan_final_reportlab.pdf", pagesize=A4)

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

    personality_data = {
        "trait_1_title": "Kecenderungan Emosi Kuat",
        "trait_1_desc": "Sangat responsif terhadap hal-hal yang memicu emosi negatif (seperti rasa khawatir, takut, atau frustrasi).",
        "trait_2_title": "Logika Kuat",
        "trait_2_desc": "Kemampuan menganalisis data/info dengan baik dan efisien dalam menyelesaikan tantangan.",
        "suitability": "KURANG SESUAI",
        "position": "Manager Marketing & Promotion",
        "reasons": [
            "Rentan terhadap cemas di kondisi dinamis",
            "Stres berlebihan berisiko muncul",
            "Butuh kepastian & rencana terukur"
        ],
        "suggestions": [
            "Manajemen Stres: Jadwal istirahat terjaga",
            "Hindari keputusan emosional",
            "Perlu dukungan tim yang kreatif"
        ],
        "tips": "Manfaatkan logika sebagai tameng untuk mengelola kecemasan, dan pilih lingkungan kerja yang memberi ruang pada prediktabilitas"
    }

    job_fit_data = [
        {"title": "Analis Data / Data Scientist", "reason": "Penggunaan data yang jelas dan metodis membantu mengurangi kecemasan dan meningkatkan kontrol terhadap hasil."},
        {"title": "Akuntansi dan Keuangan", "reason": "Membutuhkan ketelitian dan kemampuan analitis yang tinggi. Ini adalah contoh teks yang sangat panjang untuk menguji fungsi text wrapping yang diperbaiki. Teks ini harus secara otomatis dibungkus dan membuat box menjadi lebih tinggi sesuai dengan panjang konten yang ada di dalamnya."},
        {"title": "Penelitian Kuantitatif", "reason": "Bidang ini membutuhkan keterampilan logika untuk merancang eksperimen, menganalisis data, dan menarik kesimpulan."},
        {"title": "Analis Risiko", "reason": "Kecenderungan untuk mengantisipasi masalah yang terkait dengan neurotisisme bisa menjadi kekuatan dalam mengidentifikasi risiko lebih awal."},
        {"title": "Compliance Officer", "reason": "Neurotisisme yang tinggi dapat membantu dalam mengidentifikasi potensi masalah lebih awal, mencegah kesalahan atau pelanggaran yang dapat mempengaruhi kualitas."},
        {"title": "IT Analyst / Sistem Analis", "reason": "Lingkungan yang lebih terstruktur dan berbasis data membantu mengurangi kecemasan dan memberikan cara untuk merencanakan dan memecahkan masalah secara terorganisir. Teks panjang ini juga akan diuji untuk memastikan box dapat menyesuaikan tingginya dengan baik dan tidak overflow."}
    ]
    
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

    halaman_1_cover(c, biodata, "topoplot1.png", "topoplot2.png", page_num=1)
    halaman_2_traits(c, personality_data, page_num=2)
    halaman_3_job_fit(c, job_fit_data, page_num=3)
    halaman_4_disclaimer(c, disclaimer_text, page_num=4)

    c.save()
    print("PDF 'laporan_final_reportlab.pdf' berhasil dibuat!")