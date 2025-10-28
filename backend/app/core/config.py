import json
import logging
import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict
from logging.config import dictConfig
from datetime import datetime


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_record)
    
log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    # How message will look
    "formatters": {
        "json": {
            "()": JsonFormatter
        }
    },
    # Determine where logs will go
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        },
        # Log rotation for files
        "rotating_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": "secury.log",
            "maxBytes": 10485760, # 10MB
            "backupCount": 5,
        },
    },
    # Control logging behavior (Capture Debug and up)
    "loggers": {
        "app": {"handlers": ["console", "rotating_file"], "level": "DEBUG", "propagate": False},
    },
    "root": {"handlers": ["console"], "level": "DEBUG"}
}

# Apply entire config
dictConfig(log_config)

logger = logging.getLogger("app")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    SECRET_KEY: str = "083ceb3dab50bea75023667ccd881b29be0cd98e4e19213115181fe5e47d6a14" # secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 60 min * 24 h * 8 days = 8 days

    DATABASE_FILENAME: str = "database.db"
    DATABASE_URL: str = f"sqlite:///{DATABASE_FILENAME}"

settings = Settings()