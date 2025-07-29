from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color, black, white
from textwrap import wrap
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY

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
        c.setLineWidth(4)  # garis lebih tebal dari default (0.5)
        c.setStrokeColor(black)
        garis_y = PAGE_HEIGHT - 42 * mm  # posisinya di bawah alamat
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
    except:
        print(f"Gambar '{img_path}' tidak ditemukan.")
        return y_top - 100

def halaman_1_cover(c, biodata, topoplot1, topoplot2, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    # === Judul Tengah ===
    c.setFont("Times-Bold", 18)
    c.setFillColorRGB(0, 0.2, 0.6)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 150, "BRAIN WAVE PROFILING")  # turunkan dari -80 → -115
    c.setFillColor(black)

    # === Biodata ===
    c.setFont("Times-Roman", 12)
    y = PAGE_HEIGHT - 170  # diturunkan dari -95 → -135 agar tidak menabrak logo
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

def halaman_2_traits(c, data, template_path, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    try:
        c.drawImage(template_path, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT, mask='auto')
    except:
        c.setFont("Times-Bold", 12)
        c.setFillColorRGB(1, 0, 0)
        c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT / 2, f"TEMPLATE '{template_path}' TIDAK DITEMUKAN")
        c.setFillColor(black)

    c.setFont("Times-Roman", 9)
    c.setFillColor(white)
    wrap1 = wrap(data['trait_1_desc'], 45)
    wrap2 = wrap(data['trait_2_desc'], 45)

    y1, y2 = 665, 665
    for line in wrap1:
        c.drawString(27 * mm, y1, line)
        y1 -= 12
    for line in wrap2:
        c.drawString(112 * mm, y2, line)
        y2 -= 12

    c.setFont("Times-Bold", 11)
    c.setFillColor(black)
    c.drawCentredString(PAGE_WIDTH / 2, 500, f"{data['suitability']} untuk posisi")
    c.drawCentredString(PAGE_WIDTH / 2, 485, data["position"])

    c.setFont("Times-Roman", 10)
    y = 460
    for i, reason in enumerate(data['reasons']):
        c.drawString(25 * mm, y, f"{i+1}. {reason}")
        y -= 14

    y = 360
    for suggestion in data['suggestions']:
        c.drawString(25 * mm, y, f"- {suggestion}")
        y -= 14

    c.setFont("Times-Roman", 11)
    c.setFillColor(white)
    tips = wrap(data['tips'], 80)
    y = 200
    for line in tips:
        c.drawCentredString(PAGE_WIDTH / 2, y, f'"{line}"')
        y -= 14

    draw_footer(c, page_num)
    c.showPage()

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.colors import Color, black
from reportlab.lib.units import mm

def wrap_text_to_width(text, font_name, font_size, max_width):
    def break_long_word(word):
        parts = []
        current = ""
        for char in word:
            test = current + char
            if stringWidth(test, font_name, font_size) <= max_width:
                current = test
            else:
                if current:
                    parts.append(current)
                current = char
        if current:
            parts.append(current)
        return parts

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + " " + word if current_line else word
        width = stringWidth(test_line, font_name, font_size)

        if width <= max_width:
            current_line = test_line
        else:
            if stringWidth(word, font_name, font_size) > max_width:
                if current_line:
                    lines.append(current_line)
                broken = break_long_word(word)
                for part in broken[:-1]:
                    lines.append(part)
                current_line = broken[-1]
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

    if current_line:
        lines.append(current_line)

    return lines

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
    padding_top = 20  # atas dari batas box
    padding_bottom = 12  # bawah dari batas box
    min_box_height = 45 * mm

    # --- Preprocess semua data job: bungkus teks + hitung tinggi kotak ---
    box_data = []
    for job in job_data:
        max_text_width = box_width - 15  # padding kiri-kanan
        wrapped = wrap_text_to_width(job['reason'], font_name, font_size, max_text_width)
        num_lines = len(wrapped)
        content_height = padding_top + (num_lines * line_height) + padding_bottom
        dynamic_height = max(min_box_height, content_height)
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
# =========================================================
# ===== FUNGSI INI TELAH DIUBAH SEPENUHNYA ================
# =========================================================
def halaman_4_disclaimer(c, disclaimer_text, page_num):
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
            "Rentan terhadap cmas di kondisi dinamis",
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
        {"title": "Akuntansi dan Keuangan", "reason": "Membutuhkan ketelitian dan kemampuan analitis yang tinggi."},
        {"title": "Penelitian Kuantitatif", "reason": "Bidang ini membutuhkan keterampilan logika untuk merancang eksperimen, menganalisis data, dan menarik kesimpulan."},
        {"title": "Analis Risiko", "reason": "Kecenderungan untuk mengantisipasi masalah yang terkait dengan neurotisisme bisa menjadi kekuatan dalam mengidentifikasi risiko lebih awal."},
        {"title": "Compliance Officer", "reason": "Neurotisisme yang tinggi dapat membantu dalam mengidentifikasi potensi masalah lebih awal, mencegah kesalahan atau pelanggaran yang dapat mempengaruhi kualitas."},
        {"title": "IT Analyst / Sistem Analis", "reason": "Lingkungan yang lebih terstruktur dan berbasis data membantu mengurangi kecemasan dan memberikan cara untuk merencanakan dan memecahkan masalah secara terorganisir. AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}
    ]
    
    # Pastikan teks ini menjadi satu blok panjang agar paragrafnya menyatu
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
    halaman_2_traits(c, personality_data, "body.png", page_num=2)
    halaman_3_job_fit(c, job_fit_data, page_num=3)
    halaman_4_disclaimer(c, disclaimer_text, page_num=4)

    c.save()
    print("PDF 'laporan_final_reportlab.pdf' berhasil dibuat!")