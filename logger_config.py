# filename: logger_config.py

import logging

def setup_logger(logger_name, log_file, level=logging.INFO):
    """Fungsi untuk setup logger yang bisa digunakan di banyak file."""
    
    # Dapatkan logger
    logger = logging.getLogger(logger_name)
    
    # Jangan tambahkan handler jika sudah ada, untuk mencegah duplikasi log
    if not logger.handlers:
        logger.setLevel(level)
        
        # Buat handler yang akan menulis ke file
        handler = logging.FileHandler(log_file, mode='a')
        
        # Buat formatter untuk menentukan format log
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Tambahkan handler ke logger
        logger.addHandler(handler)
        
    return logger  