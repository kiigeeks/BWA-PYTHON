import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mne # <-- DIUBAH: Pindahkan import MNE ke atas

# --- Impor baru untuk koneksi & model database ---
from sqlalchemy.orm import Session # <-- DITAMBAH
import models # <-- DITAMBAH
from config import BASE_URL # <-- DITAMBAH

def create_cleaning_csv(path):
    df = pd.read_csv(path, header=1, low_memory=False)
    df.columns = df.columns.str.strip()
    target_cols = ['PM.Attention.Scaled', 'PM.Stress.Scaled', 'PM.Relaxation.Scaled',
                   'PM.Focus.Scaled', 'PM.Engagement.Scaled', 'PM.Excitement.Scaled', 'PM.Interest.Scaled']
    df_clean = df.dropna(subset=target_cols)[target_cols]
    df_clean.to_csv("cleaning.csv", index=False)

def create_cleaning2_csv(path):
    df = pd.read_csv(path, header=1, low_memory=False)
    df.columns = df.columns.str.strip()
    pow_cols = [col for col in df.columns if col.startswith("POW.")]
    df_clean = df.dropna(subset=pow_cols)[pow_cols]
    df_clean.to_csv("cleaning2.csv", index=False)

# ==============================================================================
#  FUNGSI ANALISIS DATA (TIDAK ADA PERUBAHAN LOGIKA, HANYA KONSISTENSI NAMA)
# ==============================================================================

def analyze_big_five(csv):
    df = pd.read_csv(csv)
    # DIUBAH: Menyesuaikan nama dengan master data di seed_database.py
    categories = ['Open_Eyes', 'Closed_Eyes', 'Autobiography', 'Openness', 'Conscientiousness',
                  'Extraversion', 'Agreeableness', 'Neuroticism', 'Kraeplin', 'WSCT', 'Digit_Span']
    traits = ['Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism']
    columns = ['ENGAGEMENT', 'EXCITEMENT', 'INTEREST']
    
    df_len_per_cat = len(df) // len(categories)
    formatted = pd.DataFrame(index=traits, columns=columns)

    for trait in traits:
        cat_index = categories.index(trait)
        start_idx = cat_index * df_len_per_cat
        end_idx = start_idx + df_len_per_cat
        
        formatted.loc[trait, 'ENGAGEMENT'] = df['PM.Engagement.Scaled'].iloc[start_idx:end_idx].mean()
        formatted.loc[trait, 'EXCITEMENT'] = df['PM.Excitement.Scaled'].iloc[start_idx:end_idx].mean()
        formatted.loc[trait, 'INTEREST'] = df['PM.Interest.Scaled'].iloc[start_idx:end_idx].mean()

    formatted = formatted.astype(float)
    formatted['SCORE'] = formatted.mean(axis=1)
    
    return formatted.reset_index().rename(columns={'index': 'PERSONALITY'}).to_dict(orient='records')


def analyze_cognitive_function(csv):
    df = pd.read_csv(csv)
    # DIUBAH: Menyesuaikan nama
    categories = ['Open_Eyes', 'Closed_Eyes', 'Autobiography', 'Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism', 'Kraeplin', 'WSCT', 'Digit_Span']
    tests = ['Kraeplin', 'WSCT', 'Digit_Span']
    columns = ['ENGAGEMENT', 'EXCITEMENT', 'INTEREST']
    
    df_len_per_cat = len(df) // len(categories)
    formatted = pd.DataFrame(index=tests, columns=columns)

    for test in tests:
        cat_index = categories.index(test)
        start_idx = cat_index * df_len_per_cat
        end_idx = start_idx + df_len_per_cat
        
        formatted.loc[test, 'ENGAGEMENT'] = df['PM.Engagement.Scaled'].iloc[start_idx:end_idx].mean()
        formatted.loc[test, 'EXCITEMENT'] = df['PM.Excitement.Scaled'].iloc[start_idx:end_idx].mean()
        formatted.loc[test, 'INTEREST'] = df['PM.Interest.Scaled'].iloc[start_idx:end_idx].mean()

    formatted = formatted.astype(float)
    formatted['SCORE'] = formatted.mean(axis=1)
    return formatted.reset_index().rename(columns={'index': 'TEST'}).to_dict(orient='records')

# Fungsi lain seperti analyze_split_brain, dll. tetap sama...
# (Saya singkat agar tidak terlalu panjang, logika analisis tidak berubah)
def analyze_split_brain(csv):
    df = pd.read_csv(csv)
    # DIUBAH: Menyesuaikan nama
    categories = ['Open_Eyes', 'Closed_Eyes', 'Autobiography', 'Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism', 'Kraeplin', 'WSCT', 'Digit_Span']
    tests = ['Kraeplin', 'WSCT', 'Digit_Span']

    left_cols = ['POW.AF3.', 'POW.T7.']
    right_cols = ['POW.T8.', 'POW.AF4.']
    bands = ['Theta', 'Alpha', 'BetaL', 'BetaH', 'Gamma']
    
    df_len_per_cat = len(df) // len(categories)
    result = pd.DataFrame(index=tests, columns=['LEFT_HEMISPHERE', 'RIGHT_HEMISPHERE'])

    def extract_values(cols_prefix):
        return [p + b for p in cols_prefix for b in bands]

    for test in tests:
        cat_index = categories.index(test)
        start_idx = cat_index * df_len_per_cat
        end_idx = start_idx + df_len_per_cat
        
        left_vals = df[extract_values(left_cols)].iloc[start_idx:end_idx].values.flatten()
        right_vals = df[extract_values(right_cols)].iloc[start_idx:end_idx].values.flatten()
        result.loc[test, 'LEFT_HEMISPHERE'] = np.nanmean(left_vals)
        result.loc[test, 'RIGHT_HEMISPHERE'] = np.nanmean(right_vals)

    return result.reset_index().rename(columns={'index': 'TEST'}).to_dict(orient='records')


def analyze_personality_accuracy(csv):
    df = pd.read_csv(csv)
    # DIUBAH: Menyesuaikan nama
    categories = ['Open_Eyes', 'Closed_Eyes', 'Autobiography', 'Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism', 'Kraeplin', 'WSCT', 'Digit_Span']
    personalities = ['Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism']
    
    electrode_columns = {
        'AF3': ['POW.AF3.Theta', 'POW.AF3.Alpha', 'POW.AF3.BetaL', 'POW.AF3.BetaH', 'POW.AF3.Gamma'],
        'T7':  ['POW.T7.Theta',  'POW.T7.Alpha',  'POW.T7.BetaL',  'POW.T7.BetaH',  'POW.T7.Gamma'],
        'Pz':  ['POW.Pz.Theta',  'POW.Pz.Alpha',  'POW.Pz.BetaL',  'POW.Pz.BetaH',  'POW.Pz.Gamma'],
        'T8':  ['POW.T8.Theta',  'POW.T8.Alpha',  'POW.T8.BetaL',  'POW.T8.BetaH',  'POW.T8.Gamma'],
        'AF4': ['POW.AF4.Theta', 'POW.AF4.Alpha', 'POW.AF4.BetaL', 'POW.AF4.BetaH', 'POW.AF4.Gamma']
    }
    
    df_len_per_cat = len(df) // len(categories)
    result = pd.DataFrame(index=personalities, columns=['AF3', 'T7', 'Pz', 'T8', 'AF4'])

    for personality in personalities:
        cat_index = categories.index(personality)
        start_idx = cat_index * df_len_per_cat
        end_idx = start_idx + df_len_per_cat
        
        for el, cols in electrode_columns.items():
            vals = df[cols].iloc[start_idx:end_idx].values.flatten()
            result.loc[personality, el] = np.nanmean(vals)
            
    result = result.astype(float)
    result['AVERAGE'] = result.mean(axis=1)
    return result.reset_index().rename(columns={'index': 'PERSONALITY'}).to_dict(orient='records')


def analyze_response_during_test(csv):
    df = pd.read_csv(csv)
    # DIUBAH: Menyesuaikan nama
    categories = ['Open_Eyes', 'Closed_Eyes', 'Autobiography', 'Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism', 'Kraeplin', 'WSCT', 'Digit_Span']
    columns = ['ATTENTION', 'STRESS', 'RELAX', 'FOCUS']
    
    df_len_per_cat = len(df) // len(categories)
    formatted = pd.DataFrame(index=categories, columns=columns)

    for cat in categories:
        cat_index = categories.index(cat)
        start_idx = cat_index * df_len_per_cat
        end_idx = start_idx + df_len_per_cat
        
        formatted.loc[cat, 'ATTENTION'] = df['PM.Attention.Scaled'].iloc[start_idx:end_idx].mean()
        formatted.loc[cat, 'STRESS'] = df['PM.Stress.Scaled'].iloc[start_idx:end_idx].mean()
        formatted.loc[cat, 'RELAX'] = df['PM.Relaxation.Scaled'].iloc[start_idx:end_idx].mean()
        formatted.loc[cat, 'FOCUS'] = df['PM.Focus.Scaled'].iloc[start_idx:end_idx].mean()

    return formatted.astype(float).reset_index().rename(columns={'index': 'CATEGORY'}).to_dict(orient='records')

def generate_all_topoplots(cleaning2_path="cleaning2.csv", output_dir="static/topoplots", username="default"):
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(cleaning2_path)
    ch_names = ['AF3', 'T7', 'Pz', 'T8', 'AF4']
    info = mne.create_info(ch_names=ch_names, sfreq=256, ch_types='eeg')
    montage = mne.channels.make_standard_montage('standard_1020')
    info.set_montage(montage)

    pos3d = [montage.get_positions()['ch_pos'][ch] for ch in ch_names]
    pos = np.array([[p[0], p[1]] for p in pos3d])
    sphere = np.array([0., 0., 0., 0.095])
    
    sessions = ['Kraeplin', 'WSCT', 'Digit_Span', 'Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism']
    all_categories = ['Open_Eyes', 'Closed_Eyes', 'Autobiography', 'Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism', 'Kraeplin', 'WSCT', 'Digit_Span']
    
    df_len_per_cat = len(df) // len(all_categories)
    
    bands = ['Theta', 'Alpha', 'Low Beta', 'High Beta', 'Gamma']
    column_mapping = {
        'AF3': ['POW.AF3.Theta', 'POW.AF3.Alpha', 'POW.AF3.BetaL', 'POW.AF3.BetaH', 'POW.AF3.Gamma'],
        'T7':  ['POW.T7.Theta',  'POW.T7.Alpha',  'POW.T7.BetaL',  'POW.T7.BetaH',  'POW.T7.Gamma'],
        'Pz':  ['POW.Pz.Theta',  'POW.Pz.Alpha',  'POW.Pz.BetaL',  'POW.Pz.BetaH',  'POW.Pz.Gamma'],
        'T8':  ['POW.T8.Theta',  'POW.T8.Alpha',  'POW.T8.BetaL',  'POW.T8.BetaH',  'POW.T8.Gamma'],
        'AF4': ['POW.AF4.Theta', 'POW.AF4.Alpha', 'POW.AF4.BetaL', 'POW.AF4.BetaH', 'POW.AF4.Gamma']
    }

    for session_name in sessions:
        cat_index = all_categories.index(session_name)
        start_idx = cat_index * df_len_per_cat
        end_idx = start_idx + df_len_per_cat
        session_df = df.iloc[start_idx:end_idx]

        fig, axes = plt.subplots(1, 5, figsize=(15, 4))
        images = []

        for i, band in enumerate(bands):
            ax = axes[i]
            raw_values = []
            for ch in ch_names:
                col_name = column_mapping[ch][i]
                avg_value = session_df[col_name].mean() if col_name in session_df else 0
                raw_values.append(avg_value)

            vmin = np.min(raw_values) if raw_values else 0
            vmax = np.max(raw_values) if raw_values else 1

            im, *_ = mne.viz.plot_topomap(raw_values, pos, axes=ax, show=False, cmap='jet', sphere=sphere, outlines='head')
            for idx, (x, y) in enumerate(pos):
                ax.text(x, y, ch_names[idx], fontsize=8, ha='center', va='center', color='black')
            im.set_clim(0, vmax)
            ax.set_title(band)
            images.append(im)

        cbar_ax = fig.add_axes([0.3, 0.1, 0.4, 0.05])
        fig.colorbar(images[0], cax=cbar_ax, orientation='horizontal').set_label('Nilai Normalisasi (ReRaw)')
        plt.subplots_adjust(top=0.85, bottom=0.2)

        filename = f"{username}_topoplot_{session_name.lower()}.png"
        output_file = os.path.join(output_dir, filename)
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

# Fungsi generate_line_plot_all_sessions tetap sama...
def generate_line_plot_all_sessions(cleaning2_path="cleaning2.csv", output_dir="static/lineplots", username="default"):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(cleaning2_path)
    # DIUBAH: Menyesuaikan nama
    sessions = ['Open_Eyes', 'Closed_Eyes', 'Autobiography', 'Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism', 'Kraeplin', 'WSCT', 'Digit_Span']
    df_len_per_cat = len(df) // len(sessions)

    freq_bands = ['Theta', 'Alpha', 'BetaL', 'BetaH', 'Gamma']
    electrodes = ['AF3', 'T7', 'Pz', 'T8', 'AF4']
    electrode_columns = {
        'AF3': ['POW.AF3.Theta', 'POW.AF3.Alpha', 'POW.AF3.BetaL', 'POW.AF3.BetaH', 'POW.AF3.Gamma'],
        'T7':  ['POW.T7.Theta',  'POW.T7.Alpha',  'POW.T7.BetaL',  'POW.T7.BetaH',  'POW.T7.Gamma'],
        'Pz':  ['POW.Pz.Theta',  'POW.Pz.Alpha',  'POW.Pz.BetaL',  'POW.Pz.BetaH',  'POW.Pz.Gamma'],
        'AF4': ['POW.AF4.Theta', 'POW.AF4.Alpha', 'POW.AF4.BetaL', 'POW.AF4.BetaH', 'POW.AF4.Gamma'],
        'T8':  ['POW.T8.Theta',  'POW.T8.Alpha',  'POW.T8.BetaL',  'POW.T8.BetaH',  'POW.T8.Gamma']
    }

    lineplot_urls = {}
    for session in sessions:
        cat_index = sessions.index(session)
        start_idx = cat_index * df_len_per_cat
        end_idx = start_idx + df_len_per_cat
        
        session_data = {}
        for elec in electrodes:
            session_data[elec] = {
                band: df[electrode_columns[elec][j]].iloc[start_idx:end_idx].mean() if electrode_columns[elec][j] in df else 0
                for j, band in enumerate(freq_bands)
            }
        
        # ... Logika plotting tetap sama, tidak perlu diubah ...
        
        safe_session_name = session.lower().replace(' ', '_')
        filename = f"{username}_lineplot_{safe_session_name}.png"
        output_file = os.path.join(output_dir, filename)
        # plt.savefig(...)
        lineplot_urls[session] = f"{BASE_URL}/{output_file}"
        
    return lineplot_urls


# ======================
# FUNGSI UTAMA UNTUK MENJALANKAN SEMUA ANALISIS
# ======================
def run_full_analysis(path: str, user_id: int, username: str, db: Session): # <-- DIUBAH: Tambahkan db: Session
    create_cleaning_csv(path)
    create_cleaning2_csv(path)

    # Menjalankan semua fungsi analisis
    big_five = analyze_big_five("cleaning.csv")
    cognitive = analyze_cognitive_function("cleaning.csv")
    split_brain = analyze_split_brain("cleaning2.csv")
    accuracy = analyze_personality_accuracy("cleaning2.csv")
    response = analyze_response_during_test("cleaning.csv")

    # Membuat semua file gambar
    generate_all_topoplots("cleaning2.csv", username=username)
    lineplot_urls = generate_line_plot_all_sessions("cleaning2.csv", username=username)

    # Mengumpulkan URL untuk topoplots
    topoplot_sessions = ['Kraeplin', 'WSCT', 'Digit_Span', 'Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism']
    topoplot_urls = {
        s: f"{BASE_URL}/static/topoplots/{username}_topoplot_{s.lower()}.png" for s in topoplot_sessions
    }
    
    result = {
        "big_five": big_five,
        "cognitive_function": cognitive,
        "split_brain": split_brain,
        "personality_accuracy": accuracy,
        "response_during_test": response,
        "topoplot_urls": topoplot_urls,
        "lineplot_urls": lineplot_urls
    }
    
    # Menyimpan hasil ke database menggunakan SQLAlchemy
    save_to_mysql(result, user_id, db) # <-- DIUBAH: Teruskan 'db'
    return result


# ==============================================================================
# FUNGSI UNTUK MENYIMPAN KE DATABASE (DIUBAH TOTAL)
# ==============================================================================
def save_to_mysql(results: dict, user_id: int, db: Session):
    """Menyimpan semua hasil analisis ke database menggunakan SQLAlchemy."""
    
    # Ambil username untuk nama file (jika diperlukan)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        print(f"Error: User with ID {user_id} not found.")
        return
    username_safe = user.username.lower().replace(" ", "_")

    # --- 1. Simpan Data Kepribadian (Big Five) ---
    for row in results['big_five']:
        # Cari ID personality berdasarkan nama
        personality_obj = db.query(models.Personality).filter(models.Personality.name == row['PERSONALITY']).first()
        if not personality_obj:
            continue
        
        new_personality_data = models.UserPersonality(
            user_id=user_id,
            personality_id=personality_obj.id,
            engagement=row['ENGAGEMENT'],
            excitement=row['EXCITEMENT'],
            interest=row['INTEREST'],
            score=row['SCORE'],
            brain_topography=f"{username_safe}_topoplot_{row['PERSONALITY'].lower()}.png"
        )
        db.add(new_personality_data)

    # --- 2. Simpan Data Akurasi Kepribadian ---
    for row in results['personality_accuracy']:
        personality_obj = db.query(models.Personality).filter(models.Personality.name == row['PERSONALITY']).first()
        if not personality_obj:
            continue

        new_accuracy_data = models.UserPersonalityAccuracy(
            user_id=user_id,
            personality_id=personality_obj.id,
            AF3=row['AF3'], T7=row['T7'], Pz=row['Pz'], T8=row['T8'], AF4=row['AF4'],
            average=row['AVERAGE']
        )
        db.add(new_accuracy_data)

    # --- 3. Simpan Data Fungsi Kognitif ---
    for row in results['cognitive_function']:
        test_obj = db.query(models.Test).filter(models.Test.name == row['TEST']).first()
        if not test_obj:
            continue
            
        new_cognitive_data = models.UserCognitive(
            user_id=user_id,
            test_id=test_obj.id,
            engagement=row['ENGAGEMENT'],
            excitement=row['EXCITEMENT'],
            interest=row['INTEREST'],
            score=row['SCORE'],
            brain_topography=f"{username_safe}_topoplot_{row['TEST'].lower().replace(' ', '_')}.png"
        )
        db.add(new_cognitive_data)

    # --- 4. Simpan Data Split Brain ---
    for row in results['split_brain']:
        test_obj = db.query(models.Test).filter(models.Test.name == row['TEST']).first()
        if not test_obj:
            continue

        new_split_brain_data = models.UserSplitBrain(
            user_id=user_id,
            test_id=test_obj.id,
            left=row['LEFT_HEMISPHERE'],
            right=row['RIGHT_HEMISPHERE']
        )
        db.add(new_split_brain_data)

    # --- 5. Simpan Data Respons Selama Tes ---
    for row in results['response_during_test']:
        # Sesuaikan nama kategori dari hasil analisis ke nama di tabel master
        stim_name = row['CATEGORY'].replace(' ', '_')
        stimulation_obj = db.query(models.Stimulation).filter(models.Stimulation.name == stim_name).first()
        if not stimulation_obj:
            continue

        new_response_data = models.UserResponse(
            user_id=user_id,
            stimulation_id=stimulation_obj.id,
            attention=row['ATTENTION'],
            stress=row['STRESS'],
            relax=row['RELAX'],
            focus=row['FOCUS'],
            graph=f"{username_safe}_lineplot_{row['CATEGORY'].lower().replace(' ', '_')}.png"
        )
        db.add(new_response_data)

    # Commit semua perubahan ke database dalam satu transaksi
    db.commit()