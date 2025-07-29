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

    # === Footer ===
    draw_footer(c, page_num)
    c.showPage()
    
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color, black
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

def halaman_1_cover(c, biodata, executive_summary_text, topoplot1, topoplot2, page_num):
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

    style = ParagraphStyle(
        name="JustifySmall",
        fontName="Times-Roman",
        fontSize=12,
        leading=14,
        alignment=TA_JUSTIFY,
    )

    summary_para = Paragraph(executive_summary_text, style)
    w, h = summary_para.wrap(PAGE_WIDTH - 2 * 60, 200)
    summary_para.drawOn(c, 60, y - h)

    draw_footer(c, page_num)
    c.showPage()
    
def halaman_2(c, behavior_traits_text, topoplot1, judul_topoplot1, page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    # Judul
    y_start = PAGE_HEIGHT - 170
    c.setFont("Times-Bold", 12)
    c.drawString(60, y_start, "BEHAVIOR TRAITS PROFILE")

    # Text Summary
    style = ParagraphStyle(
        name="JustifySmall",
        fontName="Times-Roman",
        fontSize=12,
        leading=14,
        alignment=TA_JUSTIFY,
    )
    summary_para = Paragraph(behavior_traits_text, style)
    max_text_width = PAGE_WIDTH - 2 * 60  # margin kiri-kanan
    w, h = summary_para.wrap(max_text_width, PAGE_HEIGHT)
    
    y_text = y_start - 20  # padding bawah judul
    summary_para.drawOn(c, 60, y_text - h)

    # --- Gambar Topoplot 1 di bawah teks ---
    padding_after_text = 20  # padding setelah paragraf
    y_topoplot1 = y_text - h - padding_after_text
    y = draw_centered_image(c, topoplot1, y_topoplot1, 180)

    judul_topoplot1 = Paragraph(judul_topoplot1,style)
    max_text_width = PAGE_WIDTH - 2 * 60  # margin kiri-kanan
    w, h = judul_topoplot1.wrap(max_text_width, PAGE_HEIGHT)
    y_judul_topoplot1 = y - h - 10  # padding atas
    judul_topoplot1.drawOn(c, 60, y_judul_topoplot1)

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

def halaman_4(c,cognitive_traits_text, page_num):
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
    
def halaman_5(c, cognitive_traits_text_2,topoplot2,judul_topoplot2 ,page_num):
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
    
def halaman_6(c, generate_ai,page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)

    # Judul
    y_start = PAGE_HEIGHT - 170
    c.setFont("Times-Bold", 12)
    c.drawString(60, y_start, "PERSON TO FIT BIDANG KERJA/USAHA")
    
    style = ParagraphStyle(
        name="JustifySmall",
        fontName="Times-Roman",
        fontSize=12,
        leading=14,
        alignment=TA_JUSTIFY,
    )
    # INPUT HASIL GENERATE AI DISINI
    #
    #
    #
    summary_para = Paragraph(generate_ai, style)
    max_text_width = PAGE_WIDTH - 2 * 60  # margin kiri-kanan
    w, h = summary_para.wrap(max_text_width, PAGE_HEIGHT)
    #
    #
    #
    y_text = y_start - 20  # padding bawah judul
    summary_para.drawOn(c, 60, y_text - h)

    draw_footer(c, page_num)
    c.showPage()

def halaman_7(c, generate_ai,page_num):
    draw_watermark(c, "cia_watermark.png")
    draw_header(c)
    
    y_start = PAGE_HEIGHT - 170
    
    style = ParagraphStyle(
        name="JustifySmall",
        fontName="Times-Roman",
        fontSize=12,
        leading=14,
        alignment=TA_JUSTIFY,
    )
    # INPUT HASIL GENERATE AI DISINI
    #
    #
    #
    summary_para = Paragraph(generate_ai, style)
    max_text_width = PAGE_WIDTH - 2 * 60  # margin kiri-kanan
    w, h = summary_para.wrap(max_text_width, PAGE_HEIGHT)
    #
    #
    #
    y_text = y_start - 20  # padding bawah judul
    summary_para.drawOn(c, 60, y_text - h)
    
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



if __name__ == "__main__":
    c = canvas.Canvas("laporan_panjang.pdf", pagesize=A4)

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

    executive_summary_text = (
        "Hasil EEG engagement dan interest menunjukan pada aktivasi tinggi pada stimulus "
        "extraversion dan stimulus digit span atau short-term memory. Individu dengan kepribadian "
        "ekstravert dan kemampuan berpikir jangka pendek (short-term thinking) “kurang sesuai” "
        "untuk posisi Staff Data Analyst. Kepribadian ekstravert biasanya lebih nyaman dalam "
        "lingkungan sosial yang dinamis dan interaktif, serta cenderung berfokus pada interaksi dengan "
        "orang lain dan pencapaian hasil langsung. Sebaliknya, pekerjaan sebagai data analyst lebih "
        "menuntut fokus pada analisis data yang mendalam, berpikir jangka panjang, serta kemampuan "
        "untuk mengelola informasi dalam waktu yang lebih lama. Pekerjaan ini juga membutuhkan "
        "ketelitian, kesabaran, dan pengambilan keputusan berbasis data yang tidak selalu dapat "
        "diputuskan dalam waktu singkat. Kemampuan berpikir short-term juga berpotensi kurang "
        "cocok untuk pekerjaan ini, yang lebih sering mengharuskan individu untuk berpikir secara "
        "strategis dan panjang dalam mengelola dataset yang besar, memikirkan pola, dan melakukan "
        "analisis yang bisa memakan waktu. Pekerjaan ini memerlukan fokus yang lebih pada akurasi "
        "dan pengolahan data daripada pencapaian hasil cepat atau keputusan yang diambil dalam "
        "waktu singkat. Posisi Staff Data Analyst akan lebih cocok untuk individu yang memiliki "
        "kepribadian introvert (lebih tenang dan fokus pada detail) dan kemampuan untuk "
        "berpikir jangka panjang, di mana mereka dapat beradaptasi dengan lingkungan kerja yang "
        "lebih tenang dan dapat mengelola proyek-proyek yang memerlukan waktu lebih lama untuk "
        "dianalisis dan diproses."
    )

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
    
    #isi hasil generate AI
    generate_ai = (
        ""
    )
    
    judul_topoplot1 = (
       "<b>Gambar 1. Topografi response Yudanta Adhipramana terhadap stimulus behavioral trait extraversion</b> "
    )
    
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
    
    behavior_traits_text_2 = (
        "Hasil penelitian EEG menunjukkan bahwa kanal-kanal yang terlibat dalam memori jangka "
        "pendek, seperti P3 dan O1, berfungsi dalam konteks pengolahan informasi visual dan verbal "
        "dalam waktu yang singkat. Peningkatan aktivitas gelombang theta dan alpha di area posterior "
        "menunjukkan bahwa otak sedang bekerja untuk memanipulasi informasi yang baru saja "
        "diterima dan menyimpannya dalam memori jangka pendek (Vogel et al., 2005). Hal ini sangat "
        "penting dalam memahami bagaimana individu dengan memori jangka pendek yang kuat dapat "
        "lebih efektif dalam pengambilan keputusan cepat dan dalam situasi yang melibatkan "
        "pengingatan informasi dengan durasi singkat."
    )
    
    judul_topoplot2 = (
        "<b>Gambar 2.Brain topografi Brain Wave Analysis Power stimulus digit span</b> "
    )
    
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

    halaman_1_cover(c, biodata, executive_summary_text, "topoplot1.png", "topoplot2.png", page_num=1)
    halaman_2(c, behavior_traits_text,"topoplot1.png", judul_topoplot1,page_num=2)
    halaman_3(c, behavior_traits_text_2, page_num=3)
    halaman_4(c, cognitive_traits_text, page_num=4)
    halaman_5(c, behavior_traits_text_2, "topoplot2.png",judul_topoplot2, page_num=5)
    halaman_6(c, generate_ai, page_num=6)
    halaman_7(c, generate_ai, page_num=7)
    halaman_8(c, referensi_text_1, page_num=8)
    halaman_11(c, disclaimer_text, page_num=12)
    c.save()
    print("PDF 'laporan_panjang.pdf' berhasil dibuat!")
