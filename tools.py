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