import logging
import os
import datetime

def get_logger(name="certificate_logger"):
    now = datetime.datetime.now()
    log_folder = f"log/{now.strftime('%d_%m_%Y')}_log"
    os.makedirs(log_folder, exist_ok=True)

    info_log_path = os.path.join(log_folder, f"{now.strftime('%d_%m_%H_%M')}_info.log")
    error_log_path = os.path.join(log_folder, f"{now.strftime('%d_%m_%H_%M')}_error.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent duplicate logs if imported multiple times

    # I'm removing any existing handlers to avoid duplicate logs.
    if logger.hasHandlers():
        logger.handlers.clear()

    # I'm adding handlers for info, error, and console output so can see logs everywhere need.
    # File handlers
    info_file_handler = logging.FileHandler(info_log_path)
    info_file_handler.setLevel(logging.INFO)
    error_file_handler = logging.FileHandler(error_log_path)
    error_file_handler.setLevel(logging.ERROR)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    info_file_handler.setFormatter(formatter)
    error_file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(info_file_handler)
    logger.addHandler(error_file_handler)
    logger.addHandler(console_handler)

    return logger

