"""
Centralized logging module with type-based coloring.
Outputs to stdout and optionally duplicates to console window.
"""
from enum import Enum
from datetime import datetime
from typing import Optional, Callable

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LogColors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    
    # Log level colors
    DEBUG = "\033[90m"      # Gray
    INFO = "\033[96m"       # Cyan
    SUCCESS = "\033[92m"    # Green
    WARNING = "\033[93m"    # Yellow
    ERROR = "\033[91m"      # Red
    
    # Timestamp color
    TIMESTAMP = "\033[90m"  # Gray

    @classmethod
    def get_color(cls, level: LogLevel) -> str:
        return getattr(cls, level.value, cls.RESET)


class Logger:
    """
    Centralized logger with console window integration.
    
    Usage:
        Logger.info("Application started")
        Logger.warning("Something might be wrong")
        Logger.error("An error occurred")
    """
    
    _console_callback: Optional[Callable[[LogLevel, str], None]] = None
    _show_timestamps: bool = True
    
    @classmethod
    def set_console_callback(cls, callback: Optional[Callable[[LogLevel, str], None]]):
        """Set the callback for sending logs to console window."""
        cls._console_callback = callback
    
    @classmethod
    def _format_message(cls, level: LogLevel, message: str, include_ansi: bool = True) -> str:
        """Format a log message with optional ANSI colors."""
        timestamp = ""
        if cls._show_timestamps:
            now = datetime.now().strftime("%H:%M:%S")
            if include_ansi:
                timestamp = f"{LogColors.TIMESTAMP}[{now}]{LogColors.RESET} "
            else:
                timestamp = f"[{now}] "
        
        level_str = f"[{level.value}]"
        
        if include_ansi:
            color = LogColors.get_color(level)
            return f"{timestamp}{color}{level_str}{LogColors.RESET} {message}"
        else:
            return f"{timestamp}{level_str} {message}"
    
    @classmethod
    def _log(cls, level: LogLevel, message: str):
        """Internal logging method."""
        # Always print to stdout with ANSI colors
        formatted_stdout = cls._format_message(level, message, include_ansi=True)
        print(formatted_stdout)
        
        # If console callback is set, send there too (without ANSI)
        if cls._console_callback:
            formatted_console = cls._format_message(level, message, include_ansi=False)
            cls._console_callback(level, formatted_console)
    
    @classmethod
    def debug(cls, message: str):
        """Log a debug message."""
        cls._log(LogLevel.DEBUG, message)
    
    @classmethod
    def info(cls, message: str):
        """Log an info message."""
        cls._log(LogLevel.INFO, message)
    
    @classmethod
    def success(cls, message: str):
        """Log a success message."""
        cls._log(LogLevel.SUCCESS, message)
    
    @classmethod
    def warning(cls, message: str):
        """Log a warning message."""
        cls._log(LogLevel.WARNING, message)
    
    @classmethod
    def error(cls, message: str):
        """Log an error message."""
        cls._log(LogLevel.ERROR, message)
