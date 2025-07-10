import logging
import sys
import os
from datetime import datetime


# Create logs directory if it doesn't exist
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Log filename with timestamp
log_filename = os.path.join(
    LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)

# Create logger instance
logger = logging.getLogger("auto_scrape_logger")
logger.setLevel(logging.DEBUG)

# Console handler for terminal output
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_format)

# File handler for logging info and higher-level messages to file
file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_format = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
file_handler.setFormatter(file_format)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.propagate = False
