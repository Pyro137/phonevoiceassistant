# app/core/logging_config.py

import os
from datetime import datetime
import logging.config
import logging
# python-json-logger kütüphanesini import edin
from pythonjsonlogger import jsonlogger # <-- Bu satırın olduğundan emin olun

# Proje kök dizinini bulmak için
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Log dizinini oluştur (eğer yoksa)
os.makedirs(LOG_DIR, exist_ok=True)

# Günlük log dosyası adı (tarihe göre)
LOG_FILE_NAME = f"app_{datetime.now().strftime('%Y%m%d')}.log"
LOG_FILE_PATH = os.path.join(LOG_DIR, LOG_FILE_NAME)

# Hata log dosyası adı (ayrı bir dosya)
ERROR_LOG_FILE_NAME = "error.log"
ERROR_LOG_FILE_PATH = os.path.join(LOG_DIR, ERROR_LOG_FILE_NAME)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            # python-json-logger'ın kendi JsonFormatter'ını kullanıyoruz
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
        },
        "error_formatter": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "json",
            "filename": LOG_FILE_PATH,
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            "encoding": "utf8",
            "level": "DEBUG",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "error_formatter",
            "filename": ERROR_LOG_FILE_PATH,
            "maxBytes": 10485760,
            "backupCount": 5,
            "encoding": "utf8",
            "level": "ERROR",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file", "error_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "app": {
            "handlers": ["console", "file", "error_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "sqlalchemy": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
        "supabase": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}