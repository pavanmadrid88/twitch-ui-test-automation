import logging
import sys
from pathlib import Path


def get_logger(name: str = "ui_test_logger"):
    """Returns a configured logger that writes to both console and file."""
    logger = logging.getLogger(name)

    # Avoid adding multiple handlers if logger is reused
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Create logs directory if needed
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "test_log.log"

    # File handler
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)

    # Stream handler (console)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
    logger.addHandler(stream_handler)

    return logger