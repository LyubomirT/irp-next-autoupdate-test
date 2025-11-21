from PySide6.QtWidgets import QCheckBox, QWidget
from PySide6.QtCore import Property, QSize, Qt, QRect
from PySide6.QtGui import QPainter, QColor, QBrush, QPen
from .brand import BrandColors

class Tumbler(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self._handle_position = 0.0
        
        # Define dimensions
        self._width = 40
        self._height = 20
        self._handle_radius = 8
        self._margin = 2
        
        # We don't do animation yet, just instant toggle

        self.setStyleSheet(self._get_stylesheet())

    def _get_stylesheet(self):
        # We use the indicator subcontrol
        return f"""
            QCheckBox {{
                spacing: 10px;
                color: {BrandColors.TEXT_PRIMARY};
            }}
            QCheckBox::indicator {{
                width: 40px;
                height: 20px;
                border-radius: 10px;
                background-color: {BrandColors.TUMBLER_BG};
            }}
            QCheckBox::indicator:checked {{
                background-color: {BrandColors.ACCENT};
            }}
            QCheckBox::indicator:unchecked:hover {{
                background-color: {BrandColors.ITEM_HOVER}; 
            }}
            /* The tumbler look is achieved via custom painting in paintEvent
            */
        """
    
    # Painted implementation of the tumbler
    
    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    def sizeHint(self):
        return QSize(self._width + 100, self._height) # Add space for text

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw text
        painter.setPen(QColor(BrandColors.TEXT_PRIMARY))
        text_rect = self.rect()
        text_rect.setLeft(self._width + 10)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.text())
        
        # Draw track
        track_rect = QRect(0, 0, self._width, self._height)
        if self.isChecked():
            bg_color = QColor(BrandColors.ACCENT)
        else:
            bg_color = QColor(BrandColors.TUMBLER_BG)
            
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, self._height / 2, self._height / 2)
        
        # Draw handle
        handle_color = QColor(BrandColors.TUMBLER_HANDLE)
        painter.setBrush(QBrush(handle_color))
        
        if self.isChecked():
            handle_x = self._width - self._handle_radius * 2 - self._margin
        else:
            handle_x = self._margin
            
        handle_y = self._margin
        handle_d = self._handle_radius * 2
        
        painter.drawEllipse(handle_x, handle_y, handle_d, handle_d)
        painter.end()

