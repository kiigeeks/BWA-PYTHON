# file: tools.py

import mne
import pandas as pd
import os
from fastapi import HTTPException

# Direktori untuk menyimpan file output
OUTPUT_DIR = "output_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def convert_edf_to_single_csv(input_path: str, original_filename: str) -> str:
    """
    Mengonversi file EDF menjadi satu file CSV.

    Args:
        input_path: Path ke file EDF sementara.
        original_filename: Nama file asli untuk nama output.

    Returns:
        Path ke file CSV yang dihasilkan.
    """
    try:
        raw = mne.io.read_raw_edf(input_path, preload=True, verbose=False)
        df = raw.to_data_frame()
        
        filename_no_spaces = original_filename.replace(' ', '_')
        
        base_filename = os.path.splitext(filename_no_spaces)[0]
        output_filename = f"{base_filename}_converted.csv"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        df.to_csv(output_path, index=False)
        return output_path
    except Exception as e:
        # Melemparkan kembali exception untuk ditangani oleh endpoint
        raise HTTPException(status_code=500, detail=f"Gagal memproses file EDF: {str(e)}")


def process_edf_with_ica_to_csv(input_path: str, original_filename: str) -> str:
    """
    Memproses file EDF dengan filter dan ICA, lalu menyimpannya ke satu file CSV.

    Args:
        input_path: Path ke file EDF sementara.
        original_filename: Nama file asli untuk nama output.

    Returns:
        Path ke file CSV yang telah diproses.
    """
    try:
        # 1. Load full EDF
        raw_full = mne.io.read_raw_edf(input_path, preload=True, verbose=False)
        
        # 2. Pilih channel EEG saja untuk ICA
        eeg_raw = raw_full.copy().pick_types(eeg=True, verbose=False)
        
        if not eeg_raw.ch_names:
            raise HTTPException(status_code=400, detail="Tidak ditemukan channel EEG di dalam file EDF.")

        # 3. Filter
        eeg_raw.filter(1., 40., fir_design='firwin', verbose=False)

        # 4. Terapkan ICA
        n_components = min(15, len(eeg_raw.ch_names) - 1)
        if n_components < 1:
            raise HTTPException(status_code=400, detail="Jumlah channel EEG tidak cukup untuk menjalankan ICA.")
            
        ica = mne.preprocessing.ICA(n_components=n_components, random_state=42, max_iter='auto')
        ica.fit(eeg_raw)
        
        # 5. Terapkan ICA ke data EEG
        ica.apply(eeg_raw, verbose=False)

        # 6. Masukkan kembali data EEG hasil ICA ke data lengkap
        for ch_name in eeg_raw.ch_names:
            if ch_name in raw_full.ch_names:
                idx_full = raw_full.ch_names.index(ch_name)
                idx_eeg = eeg_raw.ch_names.index(ch_name)
                raw_full._data[idx_full] = eeg_raw._data[idx_eeg]

        # 7. Ekspor semua channel ke CSV
        df_cleaned = raw_full.to_data_frame()
        
        filename_no_spaces = original_filename.replace(' ', '_')
        
        base_filename = os.path.splitext(filename_no_spaces)[0]
        output_filename = f"{base_filename}_ica_cleaned.csv"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        df_cleaned.to_csv(output_path, index=False)
        return output_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses file dengan ICA: {str(e)}")
    
import mne
import pandas as pd
import numpy as np
from math import ceil
from numpy.fft import fft

def process_edf_to_final_csv(edf_path: str, output_csv_path: str) -> str:
    """
    Membaca file EDF mentah, membersihkan sinyal EEG dengan ICA, menghitung 
    metrik POW dan PM, lalu menyimpannya ke satu file CSV.
    
    Args:
        edf_path (str): Path ke file .edf input.
        output_csv_path (str): Path untuk menyimpan file .csv hasil.

    Returns:
        str: Path ke file CSV yang berhasil dibuat.
    """
    print(f"Membaca file EDF: {edf_path}...")
    # LANGKAH 1: BACA FILE .EDF DAN SIAPKAN DATA
    raw_edf = mne.io.read_raw_edf(edf_path, preload=True, verbose='WARNING')
    df = raw_edf.to_data_frame(time_format=None)
    
    start_timestamp_epoch = raw_edf.info['meas_date'].timestamp()
    df['Timestamp'] = start_timestamp_epoch + df['time']
    rename_map = {'AF3': 'EEG.AF3', 'T7': 'EEG.T7', 'Pz': 'EEG.Pz', 'T8': 'EEG.T8', 'AF4': 'EEG.AF4'}
    df.rename(columns=rename_map, inplace=True)
    eeg_channels = list(rename_map.values())
    start_timestamp = df['Timestamp'].iloc[0]

    # LANGKAH 2: PRA-PEMROSESAN DENGAN ICA
    # (Menggunakan fungsi preproc dari file edf_ica_pm_pow.py)
    print("Memulai pembersihan EEG dengan ICA...")
    df_eeg_cleaned = preproc(df, eeg_channels) # Fungsi preproc harus ada/diimpor di file ini
    print("Pembersihan EEG selesai.")

    # LANGKAH 3: HITUNG POWER BANDS (POW)
    # (Menggunakan fungsi eeg_fast_transform dari file edf_ica_pm_pow.py)
    band_frequencies = [[4, 8], [8, 12], [12, 30], [20, 30], [30, 50]]
    print("\nMenghitung Power Bands (POW)...")
    df_pow = eeg_fast_transform(
        t=np.array(df['Timestamp']),
        eeg_data=np.array(df_eeg_cleaned),
        epoch_len=512, epoch_step=256,
        channels=eeg_channels, band_frequencies=band_frequencies
    )
    df_final = df_pow.copy()

    # LANGKAH 4: HITUNG METRIK PM
    print("Menghitung metrik PM...")
    BETA, ALPHA, THETA, BETA_H, GAMMA = 'Beta', 'Alpha', 'Theta', 'BetaH', 'Gamma'
    beta_cols = [col for col in df_final.columns if col.endswith(f'.{BETA}')]
    alpha_cols = [col for col in df_final.columns if col.endswith(f'.{ALPHA}')]
    theta_cols = [col for col in df_final.columns if col.endswith(f'.{THETA}')]
    beta_h_cols = [col for col in df_final.columns if col.endswith(f'.{BETA_H}')]
    gamma_cols = [col for col in df_final.columns if col.endswith(f'.{GAMMA}')]

    P_beta_db = df_final[beta_cols].mean(axis=1)
    P_alpha_db = df_final[alpha_cols].mean(axis=1)
    P_theta_db = df_final[theta_cols].mean(axis=1)
    P_beta_high_db = df_final[beta_h_cols].mean(axis=1)
    P_gamma_db = df_final[gamma_cols].mean(axis=1)

    epsilon = 1e-9
    P_beta = 10**(P_beta_db / 10)
    P_alpha = 10**(P_alpha_db / 10)
    P_theta = 10**(P_theta_db / 10)
    P_beta_high = 10**(P_beta_high_db / 10)
    P_gamma = 10**(P_gamma_db / 10)

    df_final['PM.Attention'] = P_beta / (P_alpha + P_theta + epsilon)
    df_final['PM.Engagement'] = P_beta / (P_alpha + P_theta + epsilon)
    df_final['PM.Interest'] = (P_beta + P_gamma) / (P_alpha + P_theta + epsilon)
    df_final['PM.Excitement'] = (P_gamma + P_beta_high) / (P_alpha + epsilon)
    df_final['PM.Focus'] = P_beta / (P_alpha + epsilon)
    df_final['PM.Stress'] = P_beta_high / (P_alpha + epsilon)
    df_final['PM.Relaxation'] = (P_alpha + P_theta) / (P_beta + epsilon)

    # LANGKAH 5: FINALISASI DAN SIMPAN
    df_final.insert(1, 'time', df_final['Timestamp'] - start_timestamp)
    time_cols = ['Timestamp', 'time']
    pm_cols = sorted([col for col in df_final.columns if col.startswith('PM.')])
    pow_cols = sorted([col for col in df_final.columns if col.startswith('POW.')])
    final_column_order = time_cols + pm_cols + pow_cols
    df_final = df_final[final_column_order]

    df_final.to_csv(output_csv_path, index=False)
    print(f"\nProses Selesai! File CSV komprehensif disimpan di: {output_csv_path}")
    return output_csv_path

def preproc(frame, eeg_channels):
    """
    Fungsi ini membersihkan sinyal EEG dari artefak menggunakan ICA.
    """
    print("Memulai pra-pemrosesan dengan ICA...")
    
    # 1. Tentukan informasi dasar dari data EEG Anda
    sampling_freq = 256  # Sesuai data Emotiv INSIGHT Anda
    ch_names = [ch.split('.')[-1] for ch in eeg_channels] # Mengambil nama inti: ['AF3', 'T7', 'Pz', 'T8', 'AF4']
    ch_types = ['eeg'] * len(ch_names)
    
    # Konversi data dari microvolt ke volt (kebutuhan MNE)
    eeg_data_volts = frame[eeg_channels].values.T / 1e6

    # 2. Buat objek MNE Info dan RawArray
    # Ini adalah cara kita "membungkus" data agar bisa diproses oleh MNE
    info = mne.create_info(ch_names=ch_names, sfreq=sampling_freq, ch_types=ch_types)
    raw = mne.io.RawArray(eeg_data_volts, info)
    
    # Set lokasi sensor standar untuk perangkat 5-kanal (opsional tapi bagus untuk visualisasi)
    # Anda bisa skip baris ini jika tidak ingin visualisasi, tapi ini praktik yang baik
    montage = mne.channels.make_standard_montage('standard_1020')
    raw.set_montage(montage, on_missing='warn')

    # 3. Filter sinyal sebelum ICA
    # ICA bekerja lebih baik pada data yang sudah di-bandpass filter
    raw.filter(l_freq=1., h_freq=40.)

    # 4. Inisialisasi dan jalankan ICA
    # n_components menentukan berapa "sumber" sinyal independen yang ingin kita temukan
    ica = mne.preprocessing.ICA(n_components=len(ch_names), random_state=97, max_iter='auto')
    ica.fit(raw)

    print("ICA fit selesai. Mencari komponen artefak (kedipan mata)...")

    # 5. Temukan komponen yang berhubungan dengan kedipan mata (EOG)
    # Kita akan membuat sinyal EOG "palsu" dari kanal AF3 dan AF4 untuk membantu deteksi
    # Ini adalah trik umum jika tidak ada kanal EOG khusus
    eog_indices, eog_scores = ica.find_bads_eog(raw, ch_name=['AF3', 'AF4'], threshold=1.5)
    
    if eog_indices:
        print(f"Komponen EOG yang terdeteksi: {eog_indices}")
        ica.exclude = eog_indices
    else:
        print("Tidak ada komponen kedipan mata yang signifikan terdeteksi.")

    # 6. Terapkan ICA untuk menghapus komponen artefak
    raw_cleaned = raw.copy()
    ica.apply(raw_cleaned)
    print("Artefak telah dihapus dari sinyal EEG.")

    # 7. Ambil kembali data yang sudah bersih
    cleaned_data_volts = raw_cleaned.get_data()
    
    # Konversi kembali dari volt ke microvolt
    cleaned_data_microvolts = cleaned_data_volts * 1e6
    
    # Buat DataFrame baru untuk data EEG yang sudah bersih
    cleaned_frame = pd.DataFrame(cleaned_data_microvolts.T, columns=eeg_channels)
    
    return cleaned_frame

def create_band_indices(epoch_len, band_frequencies):
    if band_frequencies is None:
        return None

    epoch_length_seconds = epoch_len / 128
    band_indicies = []
    for i in range(len(band_frequencies)):
        low_f = band_frequencies[i][0]
        high_f = band_frequencies[i][1]
        low_index = ceil(epoch_length_seconds * low_f)
        high_index = ceil(epoch_length_seconds * high_f)
        band = range(low_index, high_index)
        band_indicies.append(band)
    return band_indicies

def make_transform_columns(channels, band_frequencies):
    # Peta untuk menerjemahkan rentang frekuensi ke nama band yang benar
    band_map = {
        str([4, 8]): 'Theta',
        str([8, 12]): 'Alpha',
        str([12, 30]): 'Beta',
        str([20, 30]): 'BetaH', # Beta Tinggi
        str([30, 50]): 'Gamma'
    }

    columns = []
    if band_frequencies is not None:
        for band_range in band_frequencies:
            band_name = band_map.get(str(band_range), f"{band_range[0]}_{band_range[1]}Hz")
            for ch in channels:
                core_channel_name = ch.split('.')[-1]
                new_col_name = f"POW.{core_channel_name}.{band_name}"
                columns.append(new_col_name)
    return columns

def eeg_fast_transform(t, eeg_data, epoch_len, epoch_step, channels,
                       band_frequencies):
    band_indices = create_band_indices(epoch_len, band_frequencies)
    if band_indices is None:
        return None

    # PERBAIKAN: Hapus "+ 1" dari range untuk mencegah out-of-bounds error
    stop_range = t.shape[0] - epoch_len
    
    # start transform from 2D to 3D matrix for EEG
    ts = [[t[i], t[i+epoch_len-1]] for i in range(0, stop_range, epoch_step)] # juga ubah t[i+epoch_len] menjadi t[i+epoch_len-1] untuk konsistensi

    eeg_3d = np.dstack([eeg_data[i:i+epoch_len]
                        for i in range(0, stop_range, epoch_step)])
                        
    eeg_3d = eeg_3d - np.mean(eeg_3d, axis=0)
    hanning_window = np.hanning(eeg_3d.shape[0]) * 2
    eeg_fft_3d = (eeg_3d.T * hanning_window).T
    fourier_transform = fft(eeg_fft_3d, axis=0)/eeg_fft_3d.shape[0]
    eeg_fft_square_3d = np.absolute(fourier_transform)**2

    trans = None
    for band in band_indices:
        band_power = np.sum(eeg_fft_square_3d[band, :, :], axis=0)
        band_power = 10*np.log10(band_power/(len(band)))
        trans = band_power.T if trans is None else \
            np.concatenate((trans, band_power.T), axis=1)
            
    columns = make_transform_columns(channels, band_frequencies)

    df_features = pd.DataFrame(trans, columns=columns)
    
    # Menambahkan kolom timestamp untuk acuan
    df_features['Timestamp'] = [ts_item[0] for ts_item in ts]
    
    return df_features