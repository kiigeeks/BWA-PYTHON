import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mysql.connector


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

def analyze_big_five(csv):
    df = pd.read_csv(csv)
    categories = ['OPEN EYES', 'CLOSED EYES', 'AUTOBIOGRAPHY', 'OPENESS', 'CONSCIENTIOUSNESS',
                 'EXTRAVERSION', 'AGREEABLENESS', 'NEUROTICISM', 'KRAEPELIN TEST', 'WCST', 'DIGIT SPAN']
    traits = ['OPENESS', 'CONSCIENTIOUSNESS', 'EXTRAVERSION', 'AGREEABLENESS', 'NEUROTICISM']
    columns = ['ENGAGEMENT', 'EXCITEMENT', 'INTEREST']
    formatted = pd.DataFrame(index=categories, columns=columns)

    for i, cat in enumerate(categories):
        idx = slice(i*6, i*6+6)
        formatted.loc[cat, 'ENGAGEMENT'] = df['PM.Engagement.Scaled'].iloc[idx].mean()
        formatted.loc[cat, 'EXCITEMENT'] = df['PM.Excitement.Scaled'].iloc[idx].mean()
        formatted.loc[cat, 'INTEREST'] = df['PM.Interest.Scaled'].iloc[idx].mean()

    formatted = formatted.astype(float)
    formatted['SCORE'] = formatted.mean(axis=1)

    explanations = {
        'OPENESS': 'X memiliki kecenderungan untuk terbuka terhadap aspek penalaran dan seni. Selain itu ia juga cenderung kreatif dan memiliki ketertarikan terhadap banyak hal',
        'CONSCIENTIOUSNESS': 'X memiliki kecenderungan terhadap keteraturan dalam mengerjakan tugas. Selain itu X juga cenderung tekun dan terorganisir dalam bekerja.',
        'EXTRAVERSION': 'X merupakan orang dengan preferensi untuk aktif dan energetik secara sosial, Tidak jarang juga jika ia suka untuk berbicara dan nyaman bekerja dalam kelompok',
        'AGREEABLENESS': 'X merupakan orang dengan kecenderungan untuk dikenal baik karena kehangatan dan keramahannya terhadap sesama. Tak jarang ia juga dikenal kooperatif',
        'NEUROTICISM': 'X adalah orang yang memiliki tendensi stabilitas emosional yang tidak terlalu baik dan terkadang mungkin mencemaskan beberapa hal. Tidak jarang ia juga dikenal orang yang sensitif.'
    }

    big_five = formatted.loc[traits].copy()
    big_five['BRIEF EXPLANATION'] = [explanations[t] for t in traits]
    return big_five.reset_index().rename(columns={'index': 'PERSONALITY'}).to_dict(orient='records')

def analyze_cognitive_function(csv):
    df = pd.read_csv(csv)
    categories = ['KRAEPELIN TEST', 'WCST', 'DIGIT SPAN']
    columns = ['ENGAGEMENT', 'EXCITEMENT', 'INTEREST']
    formatted = pd.DataFrame(index=categories, columns=columns)

    offset = {
        'KRAEPELIN TEST': 8,
        'WCST': 9,
        'DIGIT SPAN': 10
    }

    for cat in categories:
        idx = slice(offset[cat]*6, offset[cat]*6+6)
        formatted.loc[cat, 'ENGAGEMENT'] = df['PM.Engagement.Scaled'].iloc[idx].mean()
        formatted.loc[cat, 'EXCITEMENT'] = df['PM.Excitement.Scaled'].iloc[idx].mean()
        formatted.loc[cat, 'INTEREST'] = df['PM.Interest.Scaled'].iloc[idx].mean()

    formatted = formatted.astype(float)
    formatted['SCORE'] = formatted.mean(axis=1)
    return formatted.reset_index().rename(columns={'index': 'TEST'}).to_dict(orient='records')

def analyze_split_brain(csv):
    df = pd.read_csv(csv)
    categories = ['KRAEPELIN TEST', 'WCST', 'DIGIT SPAN']
    left_cols = ['POW.AF3.', 'POW.T7.']
    right_cols = ['POW.T8.', 'POW.AF4.']
    bands = ['Theta', 'Alpha', 'BetaL', 'BetaH', 'Gamma']

    def extract_values(cols_prefix):
        return [p + b for p in cols_prefix for b in bands]

    result = pd.DataFrame(index=categories, columns=['LEFT_HEMISPHERE', 'RIGHT_HEMISPHERE'])

    for i, cat in enumerate(categories):
        idx = slice((8+i)*480, (8+i+1)*480)
        left_vals = df[extract_values(left_cols)].iloc[idx].values.flatten()
        right_vals = df[extract_values(right_cols)].iloc[idx].values.flatten()
        result.loc[cat, 'LEFT_HEMISPHERE'] = np.nanmean(left_vals)
        result.loc[cat, 'RIGHT_HEMISPHERE'] = np.nanmean(right_vals)

    return result.reset_index().rename(columns={'index': 'TEST'}).to_dict(orient='records')

def analyze_personality_accuracy(csv):
    df = pd.read_csv(csv)
    categories = ['OPENNESS', 'CONSCIENTIOUSNESS', 'EXTRAVERSION', 'AGREEABLENESS', 'NEUROTICISM']
    electrode_columns = {
        'AF3': ['POW.AF3.Theta', 'POW.AF3.Alpha', 'POW.AF3.BetaL', 'POW.AF3.BetaH', 'POW.AF3.Gamma'],
        'T7':  ['POW.T7.Theta',  'POW.T7.Alpha',  'POW.T7.BetaL',  'POW.T7.BetaH',  'POW.T7.Gamma'],
        'Pz':  ['POW.Pz.Theta',  'POW.Pz.Alpha',  'POW.Pz.BetaL',  'POW.Pz.BetaH',  'POW.Pz.Gamma'],
        'T8':  ['POW.T8.Theta',  'POW.T8.Alpha',  'POW.T8.BetaL',  'POW.T8.BetaH',  'POW.T8.Gamma'],
        'AF4': ['POW.AF4.Theta', 'POW.AF4.Alpha', 'POW.AF4.BetaL', 'POW.AF4.BetaH', 'POW.AF4.Gamma']
    }
    cat_idx = {
        'OPENNESS': (1440, 1920),
        'CONSCIENTIOUSNESS': (1920, 2400),
        'EXTRAVERSION': (2400, 2880),
        'AGREEABLENESS': (2880, 3360),
        'NEUROTICISM': (3360, 3840)
    }

    result = pd.DataFrame(index=categories, columns=['AF3', 'T7', 'Pz', 'T8', 'AF4'])
    for cat in categories:
        start, end = cat_idx[cat]
        for el, cols in electrode_columns.items():
            vals = df[cols].iloc[start:end].values.flatten()
            result.loc[cat, el] = np.nanmean(vals)
    result = result.astype(float)
    result['AVERAGE'] = result.mean(axis=1)
    return result.reset_index().rename(columns={'index': 'PERSONALITY'}).to_dict(orient='records')

def analyze_response_during_test(csv):
    df = pd.read_csv(csv)
    categories = ['OPEN EYES', 'CLOSED EYES', 'AUTOBIOGRAPHY', 'OPENESS', 'CONSCIENTIOUSNESS',
                 'EXTRAVERSION', 'AGREEABLENESS', 'NEUROTICISM', 'KRAEPELIN TEST', 'WCST', 'DIGIT SPAN']
    columns = ['ATTENTION', 'STRESS', 'RELAX', 'FOCUS']
    formatted = pd.DataFrame(index=categories, columns=columns)

    for i, cat in enumerate(categories):
        idx = slice(i*6, i*6+6)
        formatted.loc[cat, 'ATTENTION'] = df['PM.Attention.Scaled'].iloc[idx].mean()
        formatted.loc[cat, 'STRESS'] = df['PM.Stress.Scaled'].iloc[idx].mean()
        formatted.loc[cat, 'RELAX'] = df['PM.Relaxation.Scaled'].iloc[idx].mean()
        formatted.loc[cat, 'FOCUS'] = df['PM.Focus.Scaled'].iloc[idx].mean()

    return formatted.astype(float).reset_index().rename(columns={'index': 'CATEGORY'}).to_dict(orient='records')

def generate_all_topoplots(cleaning2_path="cleaning2.csv", output_dir="static/topoplots", username="default"):
    import os
    import matplotlib.pyplot as plt
    import mne
    import pandas as pd
    import numpy as np

    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(cleaning2_path)
    ch_names = ['AF3', 'T7', 'Pz', 'T8', 'AF4']
    info = mne.create_info(ch_names=ch_names, sfreq=256, ch_types='eeg')
    montage = mne.channels.make_standard_montage('standard_1020')
    info.set_montage(montage)

    pos3d = [montage.get_positions()['ch_pos'][ch] for ch in ch_names]
    pos = np.array([[p[0], p[1]] for p in pos3d])
    sphere = np.array([0., 0., 0., 0.095])

    # Gabungkan semua sesi (cognitive + big five)
    sessions = {
        # Cognitive Function Test
        'KRAEPELIN_TEST': (3840, 4320),
        'WCST': (4320, 4800),
        'DIGIT_SPAN': (4800, 5280),
        # Big Five
        'OPENNESS': (1440, 1920),
        'CONSCIENTIOUSNESS': (1920, 2400),
        'EXTRAVERSION': (2400, 2880),
        'AGREEABLENESS': (2880, 3360),
        'NEUROTICISM': (3360, 3840)
    }

    bands = ['Theta', 'Alpha', 'Low Beta', 'High Beta', 'Gamma']
    column_mapping = {
        'AF3': ['POW.AF3.Theta', 'POW.AF3.Alpha', 'POW.AF3.BetaL', 'POW.AF3.BetaH', 'POW.AF3.Gamma'],
        'T7':  ['POW.T7.Theta',  'POW.T7.Alpha',  'POW.T7.BetaL',  'POW.T7.BetaH',  'POW.T7.Gamma'],
        'Pz':  ['POW.Pz.Theta',  'POW.Pz.Alpha',  'POW.Pz.BetaL',  'POW.Pz.BetaH',  'POW.Pz.Gamma'],
        'T8':  ['POW.T8.Theta',  'POW.T8.Alpha',  'POW.T8.BetaL',  'POW.T8.BetaH',  'POW.T8.Gamma'],
        'AF4': ['POW.AF4.Theta', 'POW.AF4.Alpha', 'POW.AF4.BetaL', 'POW.AF4.BetaH', 'POW.AF4.Gamma']
    }

    for session_name, (start_idx, end_idx) in sessions.items():
        session_df = df.iloc[start_idx:end_idx]
        if session_df.empty:
            continue

        fig, axes = plt.subplots(1, 5, figsize=(15, 4))
        images = []

        for i, band in enumerate(bands):
            ax = axes[i]
            raw_values = []
            for ch in ch_names:
                col_name = column_mapping[ch][i]
                avg_value = session_df[col_name].mean() if col_name in session_df else 0
                raw_values.append(avg_value)

            raw_values = np.array(raw_values)
            mean = raw_values.mean()
            std = raw_values.std()
            normalized = (raw_values - mean) / std if std > 0 else np.zeros_like(raw_values)
            if normalized.max() != normalized.min():
                normalized = (normalized - normalized.min()) / (normalized.max() - normalized.min()) * 2
            else:
                normalized = np.ones_like(normalized)

            im, *_ = mne.viz.plot_topomap(normalized, pos, axes=ax, show=False,
                                          cmap='jet', sphere=sphere, outlines='head')
            for idx, (x, y) in enumerate(pos):
                ax.text(x, y, ch_names[idx], fontsize=8, ha='center', va='center', color='black')
            im.set_clim(0, 2)
            ax.set_title(band)
            images.append(im)

        cbar_ax = fig.add_axes([0.3, 0.1, 0.4, 0.05])
        cbar = fig.colorbar(images[0], cax=cbar_ax, orientation='horizontal')
        cbar.set_label('Nilai Normalisasi (ReRaw)')
        plt.subplots_adjust(top=0.85, bottom=0.2)

        filename = f"{username}_topoplot_{session_name.lower()}.png"
        output_file = os.path.join(output_dir, filename)

        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
def generate_line_plot_all_sessions(cleaning2_path="cleaning2.csv", output_dir="static/lineplots", username="default"):
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import os

    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(cleaning2_path)

    sessions = [
        'OPEN EYES', 'CLOSED EYES', 'AUTOBIOGRAPHY',
        'OPENNESS', 'CONSCIENTIOUSNESS', 'EXTRAVERSION',
        'AGREEABLENESS', 'NEUROTICISM', 'KRAEPELIN TEST', 'WCST', 'DIGIT SPAN'
    ]

    freq_bands = ['Theta', 'Alpha', 'BetaL', 'BetaH', 'Gamma']
    electrodes = ['AF3', 'T7', 'PZ', 'AF4', 'T8']
    electrode_columns = {
        'AF3': ['POW.AF3.Theta', 'POW.AF3.Alpha', 'POW.AF3.BetaL', 'POW.AF3.BetaH', 'POW.AF3.Gamma'],
        'T7':  ['POW.T7.Theta',  'POW.T7.Alpha',  'POW.T7.BetaL',  'POW.T7.BetaH',  'POW.T7.Gamma'],
        'PZ':  ['POW.Pz.Theta',  'POW.Pz.Alpha',  'POW.Pz.BetaL',  'POW.Pz.BetaH',  'POW.Pz.Gamma'],
        'AF4': ['POW.AF4.Theta', 'POW.AF4.Alpha', 'POW.AF4.BetaL', 'POW.AF4.BetaH', 'POW.AF4.Gamma'],
        'T8':  ['POW.T8.Theta',  'POW.T8.Alpha',  'POW.T8.BetaL',  'POW.T8.BetaH',  'POW.T8.Gamma']
    }

    lineplot_urls = {}

    for i, session in enumerate(sessions):
        start, end = i * 480, (i + 1) * 480
        session_data = {}

        for elec in electrodes:
            session_data[elec] = {}
            for j, band in enumerate(freq_bands):
                col = electrode_columns[elec][j]
                session_data[elec][band] = df[col].iloc[start:end].mean() if col in df else 0

        left_electrodes = ['AF3', 'T7']
        right_electrodes = ['T8', 'AF4']

        score_left = {band: np.mean([session_data[el][band] for el in left_electrodes]) for band in freq_bands}
        score_right = {band: np.mean([session_data[el][band] for el in right_electrodes]) for band in freq_bands}

        x_labels = ['AF3', 'T7', 'PZ', 'AF4', 'T8', 'Score Left', 'Score Right']
        x_pos = np.arange(len(x_labels))

        band_values = {
            band: [
                session_data['AF3'][band], session_data['T7'][band],
                session_data['PZ'][band], session_data['AF4'][band],
                session_data['T8'][band], score_left[band], score_right[band]
            ] for band in freq_bands
        }

        plt.figure(figsize=(12, 8))
        colors = {'Theta': 'cyan', 'Alpha': 'magenta', 'BetaL': 'green', 'BetaH': 'red', 'Gamma': 'blue'}

        for band in freq_bands:
            plt.plot(x_pos, band_values[band], 'o-', color=colors[band], linewidth=2, markersize=8, label=f'{session} {band}')
            for i, val in enumerate(band_values[band]):
                plt.text(x_pos[i], val + 0.2, f'{val:.2f}', ha='center', va='bottom', fontsize=8)

        plt.xlabel('Electrode / Score', fontsize=12)
        plt.ylabel('Average Value', fontsize=12)
        plt.title(f'EEG Recording - {session}', fontsize=14, fontweight='bold')
        plt.xticks(x_pos, x_labels)
        plt.legend(loc='upper right', fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        safe_session = session.lower().replace(" ", "_")
        filename = f"{username}_lineplot_{safe_session}.png"
        output_file = os.path.join(output_dir, filename)
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        lineplot_urls[session] = f"http://127.0.0.1:8000/{output_file}"

    return lineplot_urls


import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mysql.connector

# --- Analisis dan visualisasi tetap sama ---
# (semua fungsi dari create_cleaning_csv sampai generate_line_plot_all_sessions tidak diubah)

def create_user_and_return_id(data):
    """
    Simpan data user ke tabel `users` dan kembalikan ID yang baru dibuat.
    """
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="brainwave_db"
    )
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (fullname, username, password, company, gender, age, address, test_date, test_location)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data['fullname'],
        data['username'],
        data['password'],
        data['company'],
        data['gender'],
        data['age'],
        data['address'],
        data['test_date'],
        data['test_location']
    ))

    conn.commit()
    user_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return user_id

# ======================
# 4. RUN ANALYSIS UTAMA
# ======================
def run_full_analysis(path: str, user_id: int, username: str):
    create_cleaning_csv(path)
    create_cleaning2_csv(path)

    big_five = analyze_big_five("cleaning.csv")
    cognitive = analyze_cognitive_function("cleaning.csv")
    split_brain = analyze_split_brain("cleaning2.csv")
    accuracy = analyze_personality_accuracy("cleaning2.csv")
    response = analyze_response_during_test("cleaning.csv")

    generate_all_topoplots("cleaning2.csv", username=username)
    lineplot_urls = generate_line_plot_all_sessions("cleaning2.csv", username=username)

    topoplot_urls = {
        s.upper(): f"http://127.0.0.1:8000/static/topoplots/{username}_topoplot_{s}.png"
        for s in ['kraepelin_test', 'wcst', 'digit_span','openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
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

    save_to_mysql(result, user_id)
    return result

# ======================
# 5. SAVE KE DATABASE BARU (SESUAI ERD BARU)
# ======================
def save_to_mysql(results, user_id):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="brainwave_db"
    )
    cursor = conn.cursor()

    # Ambil nama user untuk digunakan sebagai prefix nama file
    cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return {"error": f"User with id {user_id} not found"}
    username = user_row[0].lower().replace(" ", "_")

    # BIG FIVE
    for row in results['big_five']:
        cursor.execute("SELECT id FROM personalities WHERE name = %s", (row['PERSONALITY'],))
        pid = cursor.fetchone()
        if not pid: continue
        personality_id = pid[0]

        cursor.execute("""
            INSERT INTO user_personalities (user_id, personality_id, engagement, excitement, interest, score, brain_topography)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, personality_id, row['ENGAGEMENT'], row['EXCITEMENT'], row['INTEREST'], row['SCORE'], f"{username}_topoplot_{row['PERSONALITY'].lower()}.png"
        ))

    # COGNITIVE FUNCTION
    for row in results['cognitive_function']:
        cursor.execute("SELECT id FROM tests WHERE name = %s", (row['TEST'],))
        tid = cursor.fetchone()
        if not tid: continue
        test_id = tid[0]

        cursor.execute("""
            INSERT INTO user_cognitive (user_id, test_id, engagement, excitement, interest, score, brain_topography)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, test_id, row['ENGAGEMENT'], row['EXCITEMENT'], row['INTEREST'], row['SCORE'], f"{username}_topoplot_{row['TEST'].lower().replace(' ', '_')}.png"
        ))

    # SPLIT BRAIN
    for row in results['split_brain']:
        cursor.execute("SELECT id FROM tests WHERE name = %s", (row['TEST'],))
        tid = cursor.fetchone()
        if not tid: continue
        test_id = tid[0]

        cursor.execute("""
            INSERT INTO user_split_brain (user_id, test_id, `left`, `right`)
            VALUES (%s, %s, %s, %s)
        """, (
            user_id, test_id, row['LEFT_HEMISPHERE'], row['RIGHT_HEMISPHERE']
        ))

    # PERSONALITY ACCURACY
    for row in results['personality_accuracy']:
        cursor.execute("SELECT id FROM personalities WHERE name = %s", (row['PERSONALITY'],))
        pid = cursor.fetchone()
        if not pid: continue
        personality_id = pid[0]

        cursor.execute("""
            INSERT INTO user_personality_accuracies (user_id, personality_id, AF3, T7, Pz, T8, AF4, average)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, personality_id, row['AF3'], row['T7'], row['Pz'], row['T8'], row['AF4'], row['AVERAGE']
        ))

    # RESPONSE
    for row in results['response_during_test']:
        cursor.execute("SELECT id FROM stimulations WHERE name = %s", (row['CATEGORY'],))
        stim = cursor.fetchone()
        if not stim: continue
        stim_id = stim[0]

        cursor.execute("""
            INSERT INTO user_response (user_id, stimulation_id, attention, stress, relax, focus, graph)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, stim_id, row['ATTENTION'], row['STRESS'], row['RELAX'], row['FOCUS'],
            f"{username}_lineplot_{row['CATEGORY'].lower().replace(' ', '_')}.png"
        ))

    conn.commit()
    cursor.close()
    conn.close()
