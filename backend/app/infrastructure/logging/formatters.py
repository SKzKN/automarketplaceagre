import json
import logging
from datetime import datetime
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    """JSON log formatter for production use."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        # Add module info
        if record.module:
            log_data["module"] = record.module
        
        # Add function name
        if record.funcName:
            log_data["function"] = record.funcName
        
        # Add line number
        if record.lineno:
            log_data["line"] = record.lineno
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


class HumanFormatter(logging.Formatter):
    """Human-readable log formatter for development."""
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def __init__(self, include_timestamp: bool = True, include_module: bool = True, use_colors: bool = True):
        self.include_timestamp = include_timestamp
        self.include_module = include_module
        self.use_colors = use_colors
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        parts = []
        
        # Timestamp
        if self.include_timestamp:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            parts.append(f"[{timestamp}]")
        
        # Level with color
        level = record.levelname
        if self.use_colors:
            color = self.COLORS.get(level, "")
            parts.append(f"{color}{level:8}{self.RESET}")
        else:
            parts.append(f"{level:8}")
        
        # Module
        if self.include_module:
            parts.append(f"[{record.name}]")
        
        # Message
        parts.append(record.getMessage())
        
        result = " ".join(parts)
        
        # Add exception info if present
        if record.exc_info:
            result += "\n" + self.formatException(record.exc_info)
        
        return result
