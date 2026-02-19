import logging
import sys
from typing import Optional

from .config import LogConfig, LogFormat, get_log_config
from .formatters import JsonFormatter, HumanFormatter


_configured = False


def setup_logging(config: Optional[LogConfig] = None) -> None:
    global _configured
    
    if _configured:
        return
    
    config = config or get_log_config()
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.log_level.value)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(config.log_level.value)
    
    # Set formatter based on config
    if config.log_format == LogFormat.JSON:
        formatter = JsonFormatter()
    else:
        formatter = HumanFormatter(
            include_timestamp=config.log_include_timestamp,
            include_module=config.log_include_module,
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if configured
    if config.log_file:
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setLevel(config.log_level.value)
        file_handler.setFormatter(JsonFormatter())  # Always use JSON for file logs
        root_logger.addHandler(file_handler)
    
    # Set levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
