"""
Console window for displaying application logs.
QT-based window with black background and colored text.
"""
from PySide6.QtWidgets import QMainWindow, QPlainTextEdit, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCharFormat, QColor, QFont

from .brand import BrandColors


class ConsoleWindow(QMainWindow):
    """
    A console window that displays colored log output.
    Cannot be closed manually - only closes when settings toggle is off.
    """
    
    MAX_LINES = 500
    
    # Color mapping for log levels
    LEVEL_COLORS = {
        "DEBUG": "#808080",     # Gray
        "INFO": "#00CED1",      # Cyan
        "SUCCESS": "#5af043",   # Green (from brand)
        "WARNING": "#f0c243",   # Yellow/Orange (from brand)
        "ERROR": "#f04943",     # Red (from brand)
    }
    
    def __init__(self, parent=None):
        # Pass None as parent to make it a top-level window with its own taskbar icon
        super().__init__(None)
        self.setWindowTitle("Console")
        self.resize(700, 400)
        
        # Remove close button but keep minimize and maximize
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.CustomizeWindowHint |
            Qt.WindowTitleHint
        )
        
        self._init_ui()
        self._line_count = 0
    
    def _init_ui(self):
        """Initialize the UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Text display area
        self.text_area = QPlainTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Styling
        font = QFont("Consolas", 10)
        self.text_area.setFont(font)
        
        self.text_area.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: #0c0c0c;
                color: {BrandColors.TEXT_PRIMARY};
                border: none;
                padding: 8px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: #1a1a1a;
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: #444444;
                min-height: 20px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #555555;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar:horizontal {{
                border: none;
                background: #1a1a1a;
                height: 12px;
                margin: 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background: #444444;
                min-width: 20px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: #555555;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)
        
        layout.addWidget(self.text_area)
        
        # Main window styling
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #0c0c0c;
            }}
        """)
    
    def _get_color_for_level(self, level_str: str) -> str:
        """Get the hex color for a log level."""
        return self.LEVEL_COLORS.get(level_str, BrandColors.TEXT_PRIMARY)
    
    @Slot(str, str)
    def append_log(self, level_name: str, message: str):
        """
        Append a log message with appropriate coloring.
        
        Args:
            level_name: The log level name (DEBUG, INFO, etc.)
            message: The formatted log message
        """
        color = self._get_color_for_level(level_name)
        
        # Use HTML formatting for colored text
        html_message = f'<span style="color: {color};">{message}</span>'
        self.text_area.appendHtml(html_message)
        
        self._line_count += 1
        
        # Trim old lines if exceeded max
        if self._line_count > self.MAX_LINES:
            self._trim_lines()
        
        # Auto-scroll to bottom
        scrollbar = self.text_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _trim_lines(self):
        """Remove oldest lines to stay within MAX_LINES limit."""
        cursor = self.text_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        
        # Calculate how many lines to remove
        lines_to_remove = self._line_count - self.MAX_LINES
        
        for _ in range(lines_to_remove):
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor)
            cursor.movePosition(cursor.MoveOperation.StartOfLine, cursor.MoveMode.KeepAnchor)
        
        # Include the newline
        cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        
        self._line_count = self.MAX_LINES
    
    def clear(self):
        """Clear all log content."""
        self.text_area.clear()
        self._line_count = 0
    
    def closeEvent(self, event):
        """Prevent manual closing - always ignore close events."""
        event.ignore()
    
    def force_close(self):
        """Force close the window (called when settings toggle is off)."""
        # Temporarily restore close button behavior
        self.setWindowFlags(self.windowFlags() | Qt.WindowCloseButtonHint)
        self.close()
