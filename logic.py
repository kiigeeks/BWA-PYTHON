# logic.py (Versi Refactor dengan Segmentasi Waktu - Tanpa Line Plot)
import mne
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import mysql.connector
from config import settings # Pastikan config diimpor

# ==================================
# 1. PERSIAPAN DATA (MODIFIKASI)
# ==================================

def create_cleaning_csv(path):
    """
    Membuat cleaning.csv yang berisi kolom PM dan 'time'.
    """
    # Membaca dari header baris pertama (indeks 0)
    df = pd.read_csv(path, header=0, low_memory=False)
    df.columns = df.columns.str.strip()
    
    # Kolom yang dibutuhkan: semua PM dan 'time'
    pm_cols = ['PM.Attention', 'PM.Stress', 'PM.Relaxation',
               'PM.Focus', 'PM.Engagement', 'PM.Excitement', 'PM.Interest']
    
    # Pastikan semua kolom PM dan 'time' ada
    required_cols = ['time'] + pm_cols
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Kolom berikut tidak ditemukan di {path}: {missing}")

    df_clean = df.dropna(subset=required_cols)[required_cols]
    df_clean.to_csv("cleaning.csv", index=False)

def create_cleaning2_csv(path):
    """
    Membuat cleaning2.csv yang berisi kolom POW dan 'time'.
    """
    df = pd.read_csv(path, header=0, low_memory=False)
    df.columns = df.columns.str.strip()
    
    pow_cols = [col for col in df.columns if col.startswith("POW.")]
    
    required_cols = ['time'] + pow_cols
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Kolom berikut tidak ditemukan di {path}: {missing}")

    df_clean = df.dropna(subset=required_cols)[required_cols]
    df_clean.to_csv("cleaning2.csv", index=False)


# ==================================
# 2. FUNGSI ANALISIS (REFACTOR TOTAL)
# ==================================

# Mendefinisikan sesi dan rentang waktunya di satu tempat
SESSION_DEFINITIONS = {
    'OPEN EYES': (0, 60),
    'CLOSED EYES': (60, 120),
    'AUTOBIOGRAPHY': (120, 180),
    'OPENESS': (180, 240),
    'CONSCIENTIOUSNESS': (240, 300),
    'EXTRAVERSION': (300, 360),
    'AGREEABLENESS': (360, 420),
    'NEUROTICISM': (420, 480),
    'KRAEPELIN TEST': (480, 540),
    'WCST': (540, 600),
    'DIGIT SPAN': (600, 660)
}

def analyze_big_five(csv_path="cleaning.csv"):
    df = pd.read_csv(csv_path)
    traits = ['OPENESS', 'CONSCIENTIOUSNESS', 'EXTRAVERSION', 'AGREEABLENESS', 'NEUROTICISM']
    results = []

    explanations = {
        'OPENESS': 'X memiliki kecenderungan untuk terbuka terhadap aspek penalaran dan seni. Selain itu ia juga cenderung kreatif dan memiliki ketertarikan terhadap banyak hal',
        'CONSCIENTIOUSNESS': 'X memiliki kecenderungan terhadap keteraturan dalam mengerjakan tugas. Selain itu X juga cenderung tekun dan terorganisir dalam bekerja.',
        'EXTRAVERSION': 'X merupakan orang dengan preferensi untuk aktif dan energetik secara sosial, Tidak jarang juga jika ia suka untuk berbicara dan nyaman bekerja dalam kelompok',
        'AGREEABLENESS': 'X merupakan orang dengan kecenderungan untuk dikenal baik karena kehangatan dan keramahannya terhadap sesama. Tak jarang ia juga dikenal kooperatif',
        'NEUROTICISM': 'X adalah orang yang memiliki tendensi stabilitas emosional yang tidak terlalu baik dan terkadang mungkin mencemaskan beberapa hal. Tidak jarang ia juga dikenal orang yang sensitif.'
    }

    for trait in traits:
        start_time, end_time = SESSION_DEFINITIONS[trait]
        # Filter DataFrame berdasarkan rentang waktu sesi
        session_df = df[(df['time'] >= start_time) & (df['time'] < end_time)]
        
        if not session_df.empty:
            engagement = session_df['PM.Engagement'].mean()
            excitement = session_df['PM.Excitement'].mean()
            interest = session_df['PM.Interest'].mean()
            score = np.mean([engagement, excitement, interest])
            
            results.append({
                "PERSONALITY": trait,
                "ENGAGEMENT": engagement,
                "EXCITEMENT": excitement,
                "INTEREST": interest,
                "SCORE": score,
                "BRIEF_EXPLANATION": explanations[trait]
            })
            
    return results

def analyze_cognitive_function(csv_path="cleaning.csv"):
    df = pd.read_csv(csv_path)
    tests = ['KRAEPELIN TEST', 'WCST', 'DIGIT SPAN']
    results = []
    
    for test in tests:
        start_time, end_time = SESSION_DEFINITIONS[test]
        session_df = df[(df['time'] >= start_time) & (df['time'] < end_time)]
        
        if not session_df.empty:
            engagement = session_df['PM.Engagement'].mean()
            excitement = session_df['PM.Excitement'].mean()
            interest = session_df['PM.Interest'].mean()
            score = np.mean([engagement, excitement, interest])
            
            results.append({
                "TEST": test,
                "ENGAGEMENT": engagement,
                "EXCITEMENT": excitement,
                "INTEREST": interest,
                "SCORE": score,
            })
            
    return results

def analyze_split_brain(csv_path="cleaning2.csv"):
    df = pd.read_csv(csv_path)
    tests = ['KRAEPELIN TEST', 'WCST', 'DIGIT SPAN']
    
    # Ambil semua kolom untuk belahan kiri dan kanan
    left_cols = [col for col in df.columns if 'POW.AF3' in col or 'POW.T7' in col]
    right_cols = [col for col in df.columns if 'POW.T8' in col or 'POW.AF4' in col]
    
    results = []
    
    for test in tests:
        start_time, end_time = SESSION_DEFINITIONS[test]
        session_df = df[(df['time'] >= start_time) & (df['time'] < end_time)]
        
        if not session_df.empty:
            # Hitung rata-rata dari semua kolom relevan di dalam sesi
            left_mean = session_df[left_cols].values.mean()
            right_mean = session_df[right_cols].values.mean()
            
            results.append({
                "TEST": test,
                "LEFT_HEMISPHERE": left_mean,
                "RIGHT_HEMISPHERE": right_mean
            })
            
    return results

def analyze_personality_accuracy(csv_path="cleaning2.csv"):
    df = pd.read_csv(csv_path)
    personalities = ['OPENESS', 'CONSCIENTIOUSNESS', 'EXTRAVERSION', 'AGREEABLENESS', 'NEUROTICISM']
    electrodes = ['AF3', 'T7', 'Pz', 'T8', 'AF4']
    results = []

    for personality in personalities:
        start_time, end_time = SESSION_DEFINITIONS[personality]
        session_df = df[(df['time'] >= start_time) & (df['time'] < end_time)]
        
        if not session_df.empty:
            row = {"PERSONALITY": personality}
            electrode_means = []
            for el in electrodes:
                # Ambil semua kolom power untuk elektroda ini
                el_cols = [col for col in df.columns if f"POW.{el}" in col]
                el_mean = session_df[el_cols].values.mean()
                row[el] = el_mean
                electrode_means.append(el_mean)
            
            row["AVERAGE"] = np.mean(electrode_means)
            results.append(row)
            
    return results

def analyze_response_during_test(csv_path="cleaning.csv"):
    df = pd.read_csv(csv_path)
    results = []

    for category, (start_time, end_time) in SESSION_DEFINITIONS.items():
        session_df = df[(df['time'] >= start_time) & (df['time'] < end_time)]
        
        if not session_df.empty:
            results.append({
                "CATEGORY": category,
                "ATTENTION": session_df['PM.Attention'].mean(),
                "STRESS": session_df['PM.Stress'].mean(),
                "RELAX": session_df['PM.Relaxation'].mean(),
                "FOCUS": session_df['PM.Focus'].mean(),
            })
            
    return results

# ==================================
# 3. FUNGSI VISUALISASI (REFACTOR TOTAL)
# ==================================
def generate_all_topoplots(cleaning2_path="cleaning2.csv", output_dir="static/topoplots", username="default"):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(cleaning2_path)

    ch_names = ['AF3', 'T7', 'Pz', 'T8', 'AF4']
    info = mne.create_info(ch_names=ch_names, sfreq=256, ch_types='eeg')
    montage = mne.channels.make_standard_montage('standard_1020')
    info.set_montage(montage)

    sessions_to_plot = {k: v for k, v in SESSION_DEFINITIONS.items() if k not in ['OPEN EYES', 'CLOSED EYES', 'AUTOBIOGRAPHY']}

    bands_map = {
        'Theta': [col for col in df.columns if 'Theta' in col],
        'Alpha': [col for col in df.columns if 'Alpha' in col],
        'Beta': [col for col in df.columns if '.Beta' in col and 'BetaH' not in col],
        'High Beta': [col for col in df.columns if 'BetaH' in col],
        'Gamma': [col for col in df.columns if 'Gamma' in col]
    }

    for session_name, (start_time, end_time) in sessions_to_plot.items():
        session_df = df[(df['time'] >= start_time) & (df['time'] < end_time)]
        if session_df.empty:
            continue

        fig, axes = plt.subplots(1, 5, figsize=(25, 6))

        for i, (band_name, band_cols) in enumerate(bands_map.items()):
            ax = axes[i]
            # Ambil rata-rata, nilainya sudah dalam microvolt^2
            avg_values = session_df[band_cols].mean().values
            
            # Baris konversi dari dB sudah tidak diperlukan lagi
            # avg_values_microvolt = 10**(avg_values_db / 10) <-- DIHAPUS

            # Langsung gunakan nilai rata-rata untuk plot
            vmin = np.min(avg_values)
            vmax = np.max(avg_values)
            if vmin == vmax:
                vmin -= 1e-9 
                vmax += 1e-9

            im, _ = mne.viz.plot_topomap(avg_values, info, axes=ax, show=False, cmap='jet', names=ch_names)
            
            # Mengatur font nama channel di topografi
            for text in ax.texts:
                if text.get_text() in ch_names:
                    text.set_fontweight('bold')
                    text.set_fontsize(16)

            im.set_clim(vmin, vmax)
            
            cbar = fig.colorbar(im, ax=ax, orientation='horizontal', pad=0.1, shrink=0.8)
            
            # --- PERUBAHAN 3: Set label colorbar ke unit yang baru ---
            cbar.set_label('Power ($\mu V^2$)', fontsize=14, fontweight='bold')
            cbar.ax.tick_params(labelsize=12)
            
            ax.set_title(band_name, fontsize=12, fontweight='bold')

        fig.suptitle(f'Topoplot Aktivitas Otak: {session_name}', fontsize=16, y=0.98, fontweight='bold')
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])

        filename = f"{username}_topoplot_{session_name.lower().replace(' ', '_')}.png"
        output_file = os.path.join(output_dir, filename)
        plt.savefig(output_file, dpi=150)
        plt.close(fig)

def generate_roc_curves(cleaning2_path="cleaning2.csv", output_dir="static/roc_curves", username="default"):
    """
    Menghasilkan grafik ROC dengan sambungan garis yang dibulatkan agar
    terlihat lebih mulus secara visual.
    """
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(cleaning2_path)
    
    channels = ['AF3', 'T7', 'Pz', 'T8', 'AF4']
    bands_map = {
        'Theta': 'Theta',
        'Alpha': 'Alpha',
        'Beta': 'Beta',
        'Gamma': 'Gamma'
    }

    baseline_start, baseline_end = SESSION_DEFINITIONS['AUTOBIOGRAPHY']
    df_baseline = df[(df['time'] >= baseline_start) & (df['time'] < baseline_end)]

    task_sessions_names = ['OPENESS', 'CONSCIENTIOUSNESS', 'EXTRAVERSION', 'AGREEABLENESS', 'NEUROTICISM', 'KRAEPELIN TEST', 'WCST', 'DIGIT SPAN']
    
    roc_results = []

    for channel in channels:
        for band_key, band_name in bands_map.items():
            col_name = f"POW.{channel}.{band_name}"
            if col_name not in df.columns:
                continue

            plt.figure(figsize=(10, 8))
            
            for session_name in task_sessions_names:
                task_start, task_end = SESSION_DEFINITIONS[session_name]
                df_task_single = df[(df['time'] >= task_start) & (df['time'] < task_end)]

                baseline_scores = df_baseline[col_name].dropna().values
                task_scores = df_task_single[col_name].dropna().values
                
                if len(baseline_scores) == 0 or len(task_scores) == 0:
                    continue

                y_scores = np.concatenate([baseline_scores, task_scores])
                y_true = np.concatenate([np.zeros(len(baseline_scores)), np.ones(len(task_scores))])

                min_score, max_score = np.min(y_scores), np.max(y_scores)
                # Kita tetap gunakan banyak threshold agar resolusi tetap tinggi
                thresholds = np.linspace(min_score, max_score, 200)

                tpr_list, fpr_list = [], []

                for thresh in sorted(thresholds, reverse=True):
                    y_pred = (y_scores >= thresh).astype(int)
                    tp = np.sum((y_true == 1) & (y_pred == 1))
                    fp = np.sum((y_true == 0) & (y_pred == 1))
                    tn = np.sum((y_true == 0) & (y_pred == 0))
                    fn = np.sum((y_true == 1) & (y_pred == 0))
                    
                    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
                    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
                    tpr_list.append(tpr)
                    fpr_list.append(fpr)
                
                auc = np.trapz(tpr_list, fpr_list)

                # --- PERUBAHAN VISUAL DI SINI ---
                # Tambahkan solid_joinstyle='round' untuk membulatkan sudut
                plt.plot(fpr_list, tpr_list, lw=2.5, label=f'{session_name} (AUC = {auc:.2f})', solid_joinstyle='round')

            # Finalisasi plot
            plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel('False Positive Rate', fontsize=12)
            plt.ylabel('True Positive Rate', fontsize=12)
            plt.title(f'ROC: {band_key} on {channel} (Baseline vs Tasks)', fontsize=14, fontweight='bold')
            plt.legend(loc="lower right", fontsize='small')
            plt.grid(alpha=0.4)
            
            # Simpan file
            filename = f"{username}_roc_{channel}_{band_key.lower()}.png"
            output_file = os.path.join(output_dir, filename)
            plt.savefig(output_file, dpi=120)
            plt.close()
            
            # Kumpulkan hasil
            note = f"ROC Curves for {band_key} on {channel}, comparing Baseline (Autobiography) vs 8 individual Task Sessions."
            roc_results.append({"graph": output_file, "note": note})
            
    return roc_results

# ======================
# 4. RUN ANALYSIS UTAMA
# ======================
def run_full_analysis(path: str, user_id: int, username: str):
    # Fungsi ini tidak perlu banyak berubah, hanya memanggil fungsi-fungsi yang sudah di-refactor
    create_cleaning_csv(path)
    create_cleaning2_csv(path)

    big_five = analyze_big_five("cleaning.csv")
    cognitive = analyze_cognitive_function("cleaning.csv")
    split_brain = analyze_split_brain("cleaning2.csv")
    accuracy = analyze_personality_accuracy("cleaning2.csv")
    response = analyze_response_during_test("cleaning.csv")

    generate_all_topoplots("cleaning2.csv", username=username)
    roc_results = generate_roc_curves("cleaning2.csv", username=username)
    
    # --- PANGGILAN DAN PENGGUNAAN lineplot_urls DIHAPUS ---
    topoplot_sessions = ['KRAEPELIN_TEST', 'WCST', 'DIGIT_SPAN', 'OPENESS', 'CONSCIENTIOUSNESS', 'EXTRAVERSION', 'AGREEABLENESS', 'NEUROTICISM']
    topoplot_urls = {
        s.upper(): f"{settings.BASE_URL}/static/topoplots/{username}_topoplot_{s.lower()}.png"
        for s in topoplot_sessions
    }
    roc_curve_urls = {
        os.path.basename(res['graph']).replace('.png', ''): f"{settings.BASE_URL}/{res['graph']}"
        for res in roc_results
    }
    
    result = {
        "big_five": big_five,
        "cognitive_function": cognitive,
        "split_brain": split_brain,
        "personality_accuracy": accuracy,
        "response_during_test": response,
        "topoplot_urls": topoplot_urls,
        "roc_curve_urls": roc_curve_urls, # Tambahkan ke hasil
        "roc_results_db": roc_results # Data mentah untuk disimpan ke DB
    }
    save_to_mysql(result, user_id, username)
    del result["roc_results_db"]
    return result

# ======================
# 5. SAVE KE DATABASE
# ======================
def save_to_mysql(results, user_id, username): # PERBAIKAN: Terima 'username' di sini
    db = mysql.connector.connect(
        host=settings.DB_HOST, port=settings.DB_PORT, user=settings.DB_USER,
        password=settings.DB_PASSWORD, database=settings.DB_NAME
    )
    cursor = db.cursor()

    def clean_nan(value):
        if isinstance(value, float) and np.isnan(value):
            return None
        return value

    # PERBAIKAN: Definisikan semua kamus ID di bagian atas fungsi
    personality_ids = {
        'OPENESS': 1, 'CONSCIENTIOUSNESS': 2, 'EXTRAVERSION': 3,
        'AGREEABLENESS': 4, 'NEUROTICISM': 5
    }
    test_ids = {
        'KRAEPELIN TEST': 1, 'WCST': 2, 'DIGIT SPAN': 3
    }
    stimulation_ids = {
        'OPEN EYES': 1, 'CLOSED EYES': 2, 'AUTOBIOGRAPHY': 3, 'OPENESS': 4,
        'CONSCIENTIOUSNESS': 5, 'EXTRAVERSION': 6, 'AGREEABLENESS': 7,
        'NEUROTICISM': 8, 'KRAEPELIN TEST': 9, 'WCST': 10, 'DIGIT SPAN': 11
    }

    # Loop untuk 'big_five'
    for row in results['big_five']:
        personality_id = personality_ids.get(row['PERSONALITY'].upper())
        if not personality_id: continue
        cursor.execute(
            "INSERT INTO user_personalities (user_id, personality_id, engagement, excitement, interest, score, brain_topography) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (user_id, personality_id, clean_nan(row['ENGAGEMENT']), clean_nan(row['EXCITEMENT']), clean_nan(row['INTEREST']), clean_nan(row['SCORE']), f"{username}_topoplot_{row['PERSONALITY'].lower()}.png")
        )

    # Loop untuk 'personality_accuracy'
    for row in results['personality_accuracy']:
        personality_id = personality_ids.get(row['PERSONALITY'].upper())
        if not personality_id: continue
        cursor.execute(
            "INSERT INTO user_personality_accuracies (user_id, personality_id, AF3, T7, Pz, T8, AF4, average) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (user_id, personality_id, clean_nan(row['AF3']), clean_nan(row['T7']), clean_nan(row['Pz']), clean_nan(row['T8']), clean_nan(row['AF4']), clean_nan(row['AVERAGE']))
        )

    # Loop untuk 'cognitive_function'
    for row in results['cognitive_function']:
        test_id = test_ids.get(row['TEST'].upper())
        if not test_id: continue
        cursor.execute(
            "INSERT INTO user_cognitive (user_id, test_id, engagement, excitement, interest, score, brain_topography) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (user_id, test_id, clean_nan(row['ENGAGEMENT']), clean_nan(row['EXCITEMENT']), clean_nan(row['INTEREST']), clean_nan(row['SCORE']), f"{username}_topoplot_{row['TEST'].lower().replace(' ', '_')}.png")
        )

    # Loop untuk 'split_brain'
    for row in results['split_brain']:
        test_id = test_ids.get(row['TEST'].upper())
        if not test_id: continue
        cursor.execute(
            "INSERT INTO user_split_brain (user_id, test_id, `left`, `right`) VALUES (%s, %s, %s, %s)",
            (user_id, test_id, clean_nan(row['LEFT_HEMISPHERE']), clean_nan(row['RIGHT_HEMISPHERE']))
        )

    # Loop untuk 'response_during_test'
    for row in results['response_during_test']:
        stimulation_id = stimulation_ids.get(row['CATEGORY'].upper())
        if not stimulation_id: continue
        # --- PERUBAHAN: Menghapus kolom 'graph' dari query INSERT ---
        cursor.execute(
            "INSERT INTO user_response (user_id, stimulation_id, attention, stress, relax, focus) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, stimulation_id, clean_nan(row['ATTENTION']), clean_nan(row['STRESS']), clean_nan(row['RELAX']), clean_nan(row['FOCUS']))
        )

    if 'roc_results_db' in results:
        for row in results['roc_results_db']:
            graph_path = row['graph'].replace('\\', '/')
            note = row['note']
            cursor.execute(
                "INSERT INTO roc_curves (user_id, graph, note) VALUES (%s, %s, %s)",
                (user_id, graph_path, note)
            )

    db.commit()
    cursor.close()
    db.close()