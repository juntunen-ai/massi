"""
Centralized logging configuration for the Finnish Government Budget Explorer.
"""

import logging
import sys
from utils.config import LOG_LEVEL, DEBUG_MODE

def configure_logging():
    """Configure application-wide logging."""
    
    # Set log level from config
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for production
    if not DEBUG_MODE:
        file_handler = logging.FileHandler('application.log')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set library loggers to WARNING
    for logger_name in ['urllib3', 'google', 'streamlit']:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    return root_logger