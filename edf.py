import mne
import pandas as pd

# 1. Load full EDF
raw = mne.io.read_raw_edf("Heldy Dim_INSIGHT2_266538_2025.01.31T10.17.35+07.00.md.edf", preload=True)

# 2. Simpan salinan original untuk non-EEG channel
raw_full = raw.copy()

# 3. Pilih channel EEG saja untuk ICA
eeg_raw = raw.copy().pick_types(eeg=True)

# 4. Filter dulu (ICA butuh bandpass clean signal)
eeg_raw.filter(1., 40., fir_design='firwin')

# 5. Terapkan ICA
ica = mne.preprocessing.ICA(n_components=15, random_state=42)
ica.fit(eeg_raw)

# Optional: otak-atik manual sebelum apply, atau otomatis remove komponen artifak
# ica.plot_components() # <- manual pilih komponen

# 6. Terapkan ICA ke EEG
ica.apply(eeg_raw)

# 7. Masukkan kembali data EEG hasil ICA ke raw_full
for ch in eeg_raw.ch_names:
    raw_full._data[raw_full.ch_names.index(ch)] = eeg_raw._data[eeg_raw.ch_names.index(ch)]

# 8. Ekspor semua channel ke CSV
df = raw_full.to_data_frame()
df.to_csv("heldy_ica_filtered_full_channels.csv", index=False)

print("ICA applied to EEG. All channels exported to CSV.")

