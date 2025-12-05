"""
Centralized logging module with type-based coloring.
Outputs to stdout and optionally duplicates to console window.
"""
from enum import Enum
from datetime import datetime
from typing import Optional, Callable
import os
import glob

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
    
    _log_file: Optional[str] = None
    _max_file_size: int = 0
    _max_files: int = 0
    _log_dir: Optional[str] = None
    
    @classmethod
    def set_console_callback(cls, callback: Optional[Callable[[LogLevel, str], None]]):
        """Set the callback for sending logs to console window."""
        cls._console_callback = callback
        
    @classmethod
    def configure_file_logging(cls, enabled: bool, log_dir: str, max_files: int, max_size_val: int, size_unit: str):
        """Configure file logging settings."""
        if not enabled:
            cls._log_file = None
            return

        cls._log_dir = log_dir
        cls._max_files = max_files if max_files > 0 else float('inf')
        
        # Calculate max size in bytes
        multiplier = 1
        if size_unit == "KB":
            multiplier = 1024
        elif size_unit == "MB":
            multiplier = 1024 * 1024
        elif size_unit == "GB":
            multiplier = 1024 * 1024 * 1024
            
        cls._max_file_size = max_size_val * multiplier if max_size_val > 0 else float('inf')
        
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except OSError:
                print(f"Failed to create log directory: {log_dir}")
                return

        # Create new log file for this session
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cls._log_file = os.path.join(log_dir, f"log_{timestamp}.txt")
        
        # Cleanup old files
        cls._cleanup_old_files()
        
    @classmethod
    def _cleanup_old_files(cls):
        """Delete oldest files if count exceeds max_files."""
        if not cls._log_dir or cls._max_files == float('inf'):
            return
            
        try:
            files = glob.glob(os.path.join(cls._log_dir, "log_*.txt"))
            files.sort(key=os.path.getmtime)
            
            while len(files) >= cls._max_files:
                oldest = files.pop(0)
                try:
                    os.remove(oldest)
                except OSError:
                    pass
        except Exception:
            pass

    @classmethod
    def _trim_file(cls):
        """Remove lines from the beginning of the file until size is under limit."""
        if not cls._log_file or not os.path.exists(cls._log_file):
            return
            
        try:
            current_size = os.path.getsize(cls._log_file)
            if current_size <= cls._max_file_size:
                return
                
            # Read all lines
            with open(cls._log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Remove lines until size fits
            
            # Optimization: Estimate how many bytes to remove.
            bytes_to_remove = current_size - cls._max_file_size
            removed_bytes = 0
            start_index = 0
            
            for i, line in enumerate(lines):
                line_bytes = len(line.encode('utf-8'))
                removed_bytes += line_bytes
                if removed_bytes >= bytes_to_remove:
                    start_index = i + 1
                    break
            
            new_lines = lines[start_index:]
            
            with open(cls._log_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
                
        except Exception as e:
            print(f"Error trimming log file: {e}")

    @classmethod
    def _log_to_file(cls, message: str):
        """Append log message to file and manage size."""
        if not cls._log_file:
            return
            
        try:
            # We do NOT put ANSI codes in log file, they don't render well (at all)
             
            with open(cls._log_file, 'a', encoding='utf-8') as f:
                f.write(message + "\n")
                
            # Check size
            if cls._max_file_size != float('inf'):
                if os.path.getsize(cls._log_file) > cls._max_file_size:
                    cls._trim_file()
                    
        except Exception:
            # Don't crash app on logging failure
            pass

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
        if cls._console_callback or cls._log_file:
            formatted_clean = cls._format_message(level, message, include_ansi=False)
            
            if cls._console_callback:
                cls._console_callback(level, formatted_clean)
            
            if cls._log_file:
                 cls._log_to_file(formatted_clean)
    
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
