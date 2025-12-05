from PySide6.QtWidgets import QCheckBox, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QComboBox, QFrame, QPushButton, QSizePolicy
from PySide6.QtCore import Property, QSize, Qt, QRect, Signal, QEvent
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QIcon
from .brand import BrandColors

class MultiColumnRow(QWidget):
    def __init__(self, widgets, ratios=None, spacing=10, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(spacing)
        
        self.widgets = widgets
        
        for i, widget in enumerate(widgets):
            ratio = ratios[i] if ratios and i < len(ratios) else 1
            layout.addWidget(widget, stretch=ratio)

class StyledTextEdit(QFrame):
    textChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self.setCursor(Qt.IBeamCursor)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        
        # Inner Editor
        self.editor = QTextEdit()
        self.editor.setFrameShape(QFrame.NoFrame)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.editor.textChanged.connect(self.textChanged.emit)
        self.editor.installEventFilter(self) # For focus tracking
        
        layout.addWidget(self.editor)
        
        self._has_focus = False
        self._update_style()
        
    def eventFilter(self, obj, event):
        if obj == self.editor:
            if event.type() == QEvent.FocusIn:
                self._has_focus = True
                self._update_style()
            elif event.type() == QEvent.FocusOut:
                self._has_focus = False
                self._update_style()
        return super().eventFilter(obj, event)
        
    def _update_style(self):
        border_color = BrandColors.ACCENT if self._has_focus else BrandColors.INPUT_BORDER
        bg_color = BrandColors.INPUT_BG
        
        self.setStyleSheet(f"""
            StyledTextEdit {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 6px;
            }}
        """)
        
        # Inner editor style
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: {BrandColors.TEXT_PRIMARY};
                border: none;
                font-size: {BrandColors.FONT_SIZE_REGULAR};
                font-family: {BrandColors.FONT_FAMILY};
                selection-background-color: {BrandColors.ACCENT};
                selection-color: {BrandColors.TEXT_PRIMARY};
            }}
            QTextEdit:disabled {{
                color: {BrandColors.TEXT_DISABLED};
            }}
        """)

    def setPlainText(self, text):
        self.editor.setPlainText(text)
        
    def toPlainText(self):
        return self.editor.toPlainText()
        
    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.editor.setEnabled(enabled)
        # Update opacity or style if needed
        if not enabled:
            self.setStyleSheet(f"""
                StyledTextEdit {{
                    background-color: {BrandColors.INPUT_BG};
                    border: 2px solid {BrandColors.INPUT_BORDER};
                    border-radius: 6px;
                    opacity: 0.6;
                }}
            """)
        else:
            self._update_style()

class StyledComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {BrandColors.INPUT_BG};
                color: {BrandColors.TEXT_PRIMARY};
                border: 2px solid {BrandColors.INPUT_BORDER};
                border-radius: 6px;
                padding: 5px 10px;
                font-size: {BrandColors.FONT_SIZE_REGULAR};
                font-family: {BrandColors.FONT_FAMILY};
            }}
            QComboBox:hover {{
                border: 2px solid {BrandColors.ITEM_HOVER};
            }}
            QComboBox:focus {{
                border: 2px solid {BrandColors.ACCENT};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 0px;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }}
            QComboBox::down-arrow {{
                image: none; /* We could add a custom arrow here if needed */
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {BrandColors.TEXT_SECONDARY};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {BrandColors.INPUT_BG};
                color: {BrandColors.TEXT_PRIMARY};
                selection-background-color: {BrandColors.ACCENT};
                selection-color: {BrandColors.TEXT_PRIMARY};
                border: 1px solid {BrandColors.INPUT_BORDER};
                outline: none;
            }}
        """)

class Divider(QWidget):
    def __init__(self, text=None, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(10)
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        line1.setStyleSheet(f"background-color: {BrandColors.INPUT_BORDER};")
        layout.addWidget(line1)
        
        if text:
            label = QLabel(text)
            # Increased font size and centered alignment
            label.setStyleSheet(f"color: {BrandColors.TEXT_SECONDARY}; font-weight: bold; font-size: {BrandColors.FONT_SIZE_LARGE};")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            
            line2 = QFrame()
            line2.setFrameShape(QFrame.HLine)
            line2.setFrameShadow(QFrame.Sunken)
            line2.setStyleSheet(f"background-color: {BrandColors.INPUT_BORDER};")
            layout.addWidget(line2)

class Description(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setStyleSheet(f"""
            color: {BrandColors.TEXT_SECONDARY};
            font-size: {BrandColors.FONT_SIZE_REGULAR};
            padding: 5px 0;
        """)

class StyledButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {BrandColors.SIDEBAR_BG};
                color: {BrandColors.TEXT_PRIMARY};
                border: 1px solid {BrandColors.INPUT_BORDER};
                padding: 8px 16px;
                border-radius: 6px;
                font-size: {BrandColors.FONT_SIZE_REGULAR};
            }}
            QPushButton:hover {{
                background-color: {BrandColors.ITEM_HOVER};
                border: 1px solid {BrandColors.ACCENT};
            }}
            QPushButton:pressed {{
                background-color: {BrandColors.ACCENT};
            }}
        """)


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
        width = self._width
        if self.text():
            width += 10 + self.fontMetrics().horizontalAdvance(self.text())
        return QSize(width, self._height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw text
        if self.text():
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

class StyledLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._error_state = False
        self._update_style()
        
    def set_error(self, error: bool):
        self._error_state = error
        self._update_style()
        
    def _update_style(self):
        border_color = BrandColors.DANGER if self._error_state else BrandColors.INPUT_BORDER
        focus_border = BrandColors.DANGER if self._error_state else BrandColors.ACCENT
        
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BrandColors.INPUT_BG};
                color: {BrandColors.TEXT_PRIMARY};
                border: 2px solid {border_color};
                border-radius: 6px;
                padding: 8px;
                font-size: {BrandColors.FONT_SIZE_REGULAR};
                font-family: {BrandColors.FONT_FAMILY};
            }}
            QLineEdit:focus {{
                border: 2px solid {focus_border};
            }}
            QLineEdit:disabled {{
                color: {BrandColors.TEXT_DISABLED};
                border: 2px solid {BrandColors.INPUT_BORDER};
                background-color: {BrandColors.INPUT_BG};
                opacity: 0.6;
            }}
        """)
