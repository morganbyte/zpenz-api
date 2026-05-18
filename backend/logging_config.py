import logging
import logging.handlers
import json
import os
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""

    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id

        return json.dumps(log_obj)


def configure_logging():
    """Initialize structured logging for all modules."""
    env = os.getenv("ENVIRONMENT", "development")
    log_level = logging.DEBUG if env == "development" else logging.INFO

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers = []

    # Console handler (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    if env == "production":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Suppress noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name):
    """Get a logger for a specific module."""
    return logging.getLogger(name)
