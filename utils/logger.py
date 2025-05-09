"""
Centralized logging configuration for the application.
"""

import logging
import sys
from datetime import datetime
import os
from typing import Optional

def setup_logger(name: str, log_file: Optional[str] = None, level: str = 'INFO') -> logging.Logger:
    """
    Set up a logger with consistent formatting.
    
    Args:
        name (str): Logger name (usually __name__)
        log_file (str, optional): Log file path
        level (str): Logging level
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    
    # Don't add handlers if they already exist
    if logger.handlers:
        return logger
    
    # Set level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if log_file provided
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def configure_app_logging():
    """Configure application-wide logging."""
    # Create logs directory
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Generate log file name with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f"app_{timestamp}.log")
    
    # Set up main application logger
    app_logger = setup_logger('app', log_file, level='INFO')
    
    # Set up other component loggers
    setup_logger('utils.api_client', log_file, level='INFO')
    setup_logger('utils.bigquery_loader', log_file, level='INFO')
    setup_logger('models.llm_interface', log_file, level='INFO')
    setup_logger('utils.sql_executor', log_file, level='INFO')
    
    # Log initialization message
    app_logger.info("Application logging initialized")
    app_logger.info(f"Log file: {log_file}")
    
    return app_logger