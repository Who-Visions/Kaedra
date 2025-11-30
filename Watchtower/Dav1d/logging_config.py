import logging
import json
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config import CHAT_LOGS_DIR, LOGS_BUCKET_NAME, PROJECT_ID, TIMEZONE, Colors

# Ensure logs dir exists
CHAT_LOGS_DIR.mkdir(parents=True, exist_ok=True)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(TIMEZONE).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", "filename", 
                           "funcName", "levelname", "levelno", "lineno", "module", 
                           "msecs", "message", "msg", "name", "pathname", "process", 
                           "processName", "relativeCreated", "stack_info", "thread", "threadName"]:
                log_obj[key] = value
        
        return json.dumps(log_obj)

class ConsoleFormatter(logging.Formatter):
    def format(self, record):
        # Simple colored output for console
        msg = record.getMessage()
        if record.levelno >= logging.ERROR:
            return f"{Colors.NEON_RED}[ERROR] {msg}{Colors.RESET}"
        elif record.levelno >= logging.WARNING:
            return f"{Colors.GOLD}[WARN] {msg}{Colors.RESET}"
        elif record.levelno >= logging.INFO:
            # Don't prefix INFO to keep chat clean, or use a subtle prefix
            return msg
        return msg

def setup_logging(name="dav1d"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent double logging if root logger is configured
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers = []

    # JSON File Handler (Rotating)
    # Rotates at 10MB, keeps 5 backups
    log_file = CHAT_LOGS_DIR / "dav1d.json.log"
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ConsoleFormatter())
    logger.addHandler(console_handler)
    
    return logger

# Global logger instance
logger = setup_logging()
