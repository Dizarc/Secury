from pydantic_settings import BaseSettings, SettingsConfigDict
from logging.config import dictConfig
from datetime import datetime

import json
import logging

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
        # Log rotation in files
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
        "app": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False},
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

    DATABASE_FILENAME: str = "database.db"
    DATABASE_URL: str = f"sqlite:///{DATABASE_FILENAME}"

settings = Settings()