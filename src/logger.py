import logging
import os

def get_logger(name=None, log_file=None, use_rotating_file=False, max_bytes=1048576, backup_count=3):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Optionally add RotatingFileHandler
        if log_file:
            if use_rotating_file:
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
            else:
                file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    # Determine log level from env or config
    log_level_str = os.environ.get('LOG_LEVEL', None)
    if log_level_str:
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    else:
        log_level = logging.INFO
    logger.setLevel(log_level)
    return logger
