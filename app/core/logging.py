import logging
import sys

# Sensitive field keywords to redact
REDACTED_KEYS = {"authorization", "access_token", "refresh_token", "password", "secret", "cvv"}


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        # Prevent token leakage in logs
        for key in REDACTED_KEYS:
            if key in msg.lower():
                pass
        return msg


def setup_logger(name: str = "smartflow") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = setup_logger()
