from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QScrollArea, QLabel, QPushButton, QFrame, QMessageBox, QDialog,
    QLineEdit, QTextEdit, QComboBox, QGraphicsColorizeEffect
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QColor
from difflib import SequenceMatcher
import os
from config.manager import ConfigManager
from config.schema import SCHEMA, SettingType
from .brand import BrandColors
from .components import Tumbler, StyledLineEdit, StyledTextEdit, StyledComboBox, Divider, Description, StyledButton, MultiColumnRow, SettingRow, ToggleRow
from .icons import IconUtils, IconType
from utils.logger import Logger

class SettingsWindow(QMainWindow):
    settings_saved = Signal()

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("Settings")
        self.resize(900, 700)
        self.setStyleSheet(f"background-color: {BrandColors.WINDOW_BG}; color: {BrandColors.TEXT_PRIMARY};")
        
        self.unsaved_changes = False
        self.field_widgets = {} # Map "category.key" -> widget
        self.setting_rows = {} # Map "category.key" -> SettingRow (for dependency toggling)

        self._init_ui()
        self._load_values()

    def _create_field_widget(self, field, category_key):
        widget = None
        if field.type == SettingType.BOOLEAN:
            widget = Tumbler()
            widget.stateChanged.connect(self._on_setting_changed)
        elif field.type in [SettingType.STRING, SettingType.PASSWORD, SettingType.INTEGER]:
            widget = StyledLineEdit()
            if field.type == SettingType.PASSWORD:
                widget.setEchoMode(QLineEdit.Password)
            elif field.type == SettingType.INTEGER:
                from PySide6.QtGui import QIntValidator
                widget.setValidator(QIntValidator())
            widget.textChanged.connect(self._on_setting_changed)
        elif field.type == SettingType.DROPDOWN:
            widget = StyledComboBox()
            if field.options:
                widget.addItems(field.options)
            widget.currentTextChanged.connect(self._on_setting_changed)
            
            # Specific logic for formatting preset
            if field.key == "formatting_preset":
                widget.currentTextChanged.connect(self._on_preset_changed)
                
        elif field.type == SettingType.BUTTON:
            widget = StyledButton(field.label)
            # use the default value as button text if provided, else label
            btn_text = str(field.default) if field.default else field.label
            widget.setText(btn_text)
            
            if field.action == "reset_injection":
                widget.clicked.connect(self._reset_injection)
            elif field.action == "reset_formatting":
                widget.clicked.connect(self._reset_formatting)
        
        if widget:
            self.field_widgets[f"{category_key}.{field.key}"] = widget
            
        return widget

    def _iter_fields(self, fields):
        for field in fields:
            yield field
            if field.type == SettingType.ROW:
                yield from self._iter_fields(field.sub_fields)

    def _init_ui(self):

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left Sidebar (Categories + Search)
        left_widget = QWidget()
        left_widget.setFixedWidth(250)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.category_list = QListWidget()
        self.category_list.setFixedWidth(250)
        self.category_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {BrandColors.SIDEBAR_BG};
                border: none;
                outline: none;
                font-size: {BrandColors.FONT_SIZE_LARGE}; /* Applied to widget directly */
            }}
            QListWidget::item {{
                padding: 20px;
                color: {BrandColors.TEXT_SECONDARY};
                background-color: {BrandColors.CATEGORY_DEFAULT_BG};
                border-left: 4px solid {BrandColors.CATEGORY_BORDER_DEFAULT};
                margin-bottom: 2px; /* Small gap between items */
            }}
            QListWidget::item:selected {{
                background-color: {BrandColors.CATEGORY_ACTIVE_BG};
                color: {BrandColors.TEXT_PRIMARY};
                border-left: 4px solid {BrandColors.CATEGORY_ACTIVE_BORDER};
            }}
            QListWidget::item:selected:hover {{
                background-color: {BrandColors.CATEGORY_ACTIVE_BG};
                color: {BrandColors.TEXT_PRIMARY};
                border-left: 4px solid {BrandColors.CATEGORY_ACTIVE_BORDER};
            }}
            QListWidget::item:hover {{
                background-color: {BrandColors.ITEM_HOVER};
                color: {BrandColors.TEXT_PRIMARY};
            }}
        """)
        self.category_list.itemClicked.connect(self._on_category_clicked)
        left_layout.addWidget(self.category_list, 1)

        # Search bar at bottom of sidebar
        self.search_bar = QWidget()
        self.search_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {BrandColors.SIDEBAR_BG};
                border-top: 1px solid {BrandColors.INPUT_BORDER};
            }}
        """)
        search_layout = QHBoxLayout(self.search_bar)
        search_layout.setContentsMargins(8, 6, 8, 6)
        search_layout.setSpacing(6)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search settings…")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BrandColors.INPUT_BG};
                color: {BrandColors.TEXT_PRIMARY};
                border: 2px solid {BrandColors.INPUT_BORDER};
                border-radius: 6px;
                padding: 6px 10px 6px 28px;
                font-size: {BrandColors.FONT_SIZE_REGULAR};
                font-family: {BrandColors.FONT_FAMILY};
            }}
            QLineEdit:focus {{
                border: 2px solid {BrandColors.ACCENT};
            }}
        """)
        icons_base = os.path.join(os.path.dirname(__file__), "assets", "icons")
        search_icon_path = os.path.join(icons_base, "search.svg")
        self.search_input.addAction(QIcon(search_icon_path), QLineEdit.LeadingPosition)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_input, 1)

        left_layout.addWidget(self.search_bar, 0)
        main_layout.addWidget(left_widget)

        # Right Content Area
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(30, 30, 30, 30)
        
        # Scroll Area for Settings
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Connect scroll signal
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self.is_auto_scrolling = False
        
        # Custom Scrollbar Styling
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {BrandColors.WINDOW_BG};
                border: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {BrandColors.WINDOW_BG};
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: #555555;
                min-height: 20px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #666666;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 10, 0) # Add right margin for scrollbar space
        self.scroll_layout.setSpacing(BrandColors.CARD_SPACING)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        
        self.category_widgets = {} # Map category key -> widget (for scrolling)
        self.search_targets = []  # List of searchable setting widgets

        # Generate Fields
        for category in SCHEMA:
            # Add to list
            self.category_list.addItem(category.name)
            
            # Category Card
            card = QWidget()
            card.setStyleSheet(f"""
                QWidget {{
                    background-color: {BrandColors.SIDEBAR_BG};
                    border-radius: 8px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(BrandColors.CARD_PADDING, 18, BrandColors.CARD_PADDING, BrandColors.CARD_PADDING)
            card_layout.setSpacing(4)  # now SettingRow/ToggleRow have their own internal padding
            
            self.category_widgets[category.name] = card
            
            # Header
            header = QLabel(category.name)
            header.setStyleSheet(f"""
                font-size: {BrandColors.FONT_SIZE_TITLE}; 
                font-weight: bold; 
                color: {BrandColors.TEXT_PRIMARY};
                background-color: transparent;
            """)
            card_layout.addWidget(header)
            
            # Divider
            divider = QFrame()
            divider.setFrameShape(QFrame.HLine)
            divider.setFrameShadow(QFrame.Sunken)
            divider.setStyleSheet(f"background-color: {BrandColors.ITEM_SELECTED}; margin-bottom: 5px;")
            card_layout.addWidget(divider)
            
            # Fields
            for field in category.fields:
                # Handle Divider Type separately as it takes full width
                if field.type == SettingType.DIVIDER:
                    widget = Divider(field.label)
                    card_layout.addWidget(widget)
                    continue
                
                # Handle Description Type separately
                if field.type == SettingType.DESCRIPTION:
                    widget = Description(field.default)
                    card_layout.addWidget(widget)
                    continue

                # Use VBox for Textarea to give it more space
                if field.type == SettingType.TEXTAREA:
                    field_container = QWidget()
                    field_container.setStyleSheet("background-color: transparent;")
                    field_layout = QVBoxLayout(field_container)
                    field_layout.setContentsMargins(0, 10, 0, 10)
                    field_layout.setSpacing(6)
                    
                    label = QLabel(field.label)
                    label.setToolTip(field.tooltip or "")
                    # Consistent label styling with SettingRow
                    label.setStyleSheet(f"font-size: {BrandColors.FONT_SIZE_REGULAR}; font-weight: 500; color: {BrandColors.TEXT_SECONDARY}; background-color: transparent;")
                    field_layout.addWidget(label)
                    
                    widget = StyledTextEdit()
                    widget.textChanged.connect(self._on_setting_changed)
                    widget.setToolTip(field.tooltip or "")
                    field_layout.addWidget(widget)
                    self.field_widgets[f"{category.key}.{field.key}"] = widget
                    card_layout.addWidget(field_container)
                    self._add_search_target(category, field, field_container)
                    continue
                
                # Handle ROW type (multiple controls in one row)
                if field.type == SettingType.ROW:
                    sub_widgets = []
                    if field.sub_fields:
                        for sub in field.sub_fields:
                            sub_w = self._create_field_widget(sub, category.key)
                            sub_widgets.append(sub_w)
                    widget = MultiColumnRow(sub_widgets, field.ratios)
                    widget.setToolTip(field.tooltip or "")
                    self.field_widgets[f"{category.key}.{field.key}"] = widget
                    
                    # Use SettingRow for consistent layout
                    row = SettingRow(field.label, widget, field.tooltip)
                    self.setting_rows[f"{category.key}.{field.key}"] = row
                    card_layout.addWidget(row)
                    self._add_search_target(category, field, row)
                    continue
                
                # Standard field types - use appropriate row layout
                widget = self._create_field_widget(field, category.key)
                if widget:
                    # Use ToggleRow for boolean fields (compact horizontal layout)
                    # Pass tooltip as description to show it inline below the label
                    # Use SettingRow for everything else (stacked vertical layout)
                    if field.type == SettingType.BOOLEAN:
                        row = ToggleRow(field.label, widget, field.tooltip, description=field.tooltip)
                    else:
                        row = SettingRow(field.label, widget, field.tooltip)
                    self.setting_rows[f"{category.key}.{field.key}"] = row
                    card_layout.addWidget(row)
                    if field.type != SettingType.BUTTON:
                        self._add_search_target(category, field, row)
            
            self.scroll_layout.addWidget(card)

        self.scroll_area.setWidget(self.scroll_content)
        right_layout.addWidget(self.scroll_area)

        # Bottom Buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 0) # Add top margin to separate from content
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BrandColors.SIDEBAR_BG};
                color: {BrandColors.TEXT_PRIMARY};
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: {BrandColors.FONT_SIZE_REGULAR};
            }}
            QPushButton:hover {{
                background-color: {BrandColors.ITEM_HOVER};
            }}
        """)
        IconUtils.apply_icon(self.cancel_btn, IconType.CANCEL, BrandColors.TEXT_PRIMARY, size=16, y_offset=2)
        self.cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BrandColors.ACCENT};
                color: {BrandColors.TEXT_PRIMARY};
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: {BrandColors.FONT_SIZE_REGULAR};
            }}
            QPushButton:hover {{
                background-color: #4a80e0;
            }}
        """)
        IconUtils.apply_icon(self.save_btn, IconType.CONFIRM, BrandColors.TEXT_PRIMARY, size=16, y_offset=2)
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        right_layout.addLayout(button_layout)
        main_layout.addWidget(right_widget)

        # Select first category by default
        self.category_list.setCurrentRow(0)
        
        # Setup dependency tracking
        self.dependencies = {} # Map "dependency_key" -> list of "dependent_key"
        for category in SCHEMA:
            for field in self._iter_fields(category.fields):
                if field.depends:
                    if field.depends not in self.dependencies:
                        self.dependencies[field.depends] = []
                    self.dependencies[field.depends].append(f"{category.key}.{field.key}")
        
        # Debounce timer for updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(100)
        self.update_timer.timeout.connect(self._update_dependencies)

        # Debounce timer for settings search
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self._perform_search)

        # Flash state for search highlight
        self._flashed_widget = None
        self._flashed_original_style = ""
        self._flashed_original_effect = None
        self._flash_reset_timer = QTimer()
        self._flash_reset_timer.setSingleShot(True)
        self._flash_reset_timer.setInterval(1000)
        self._flash_reset_timer.timeout.connect(self._clear_flash)

    def _load_values(self):
        for category in SCHEMA:
            for field in self._iter_fields(category.fields):
                key = f"{category.key}.{field.key}"
                value = self.config_manager.get_setting(category.key, field.key)
                widget = self.field_widgets.get(key)
                
                if widget:
                    widget.blockSignals(True)
                    if field.type == SettingType.BOOLEAN:
                        widget.setChecked(bool(value))
                    elif field.type in [SettingType.STRING, SettingType.PASSWORD, SettingType.INTEGER]:
                        widget.setText(str(value) if value is not None else "")
                    elif field.type == SettingType.TEXTAREA:
                        widget.setPlainText(str(value) if value is not None else "")
                    elif field.type == SettingType.DROPDOWN:
                        if value and value in field.options:
                            widget.setCurrentText(value)
                    widget.blockSignals(False)
        
        self._update_dependencies()
        # Trigger preset logic manually after load
        preset_widget = self.field_widgets.get("formatting.formatting_preset")
        if preset_widget:
            self._on_preset_changed(preset_widget.currentText())
            
        self.unsaved_changes = False

    def _on_setting_changed(self):
        self.unsaved_changes = True
        self.update_timer.start()

    def _update_dependencies(self):
        for dep_key, dependent_keys in self.dependencies.items():
            dep_widget = self.field_widgets.get(dep_key)
            if not dep_widget:
                continue
                
            # Determine if dependency is met
            is_met = False
            if isinstance(dep_widget, Tumbler):
                is_met = dep_widget.isChecked()
            elif isinstance(dep_widget, StyledLineEdit) or isinstance(dep_widget, QLineEdit):
                is_met = bool(dep_widget.text())
            elif isinstance(dep_widget, StyledComboBox):
                is_met = bool(dep_widget.currentText())
            
            # Update dependents
            for dependent_key in dependent_keys:
                widget = self.field_widgets.get(dependent_key)
                if widget:
                    # If there's a SettingRow for this field, enable/disable the whole row
                    row = self.setting_rows.get(dependent_key)
                    if row:
                        row.setEnabled(is_met)
                    else:
                        widget.setEnabled(is_met)
                    if not is_met and isinstance(widget, StyledLineEdit):
                        widget.set_error(False) # Clear error if disabled

    def _add_search_target(self, category, field, widget):
        extra_labels = ""
        if field.type == SettingType.ROW and field.sub_fields:
            extra_labels = " ".join(sub.label for sub in field.sub_fields if sub.label)

        self.search_targets.append({
            "label_lower": (field.label or "").lower(),
            "key_lower": (field.key or "").lower(),
            "category_lower": (category.name or "").lower(),
            "category_key_lower": (category.key or "").lower(),
            "extra_lower": extra_labels.lower(),
            "widget": widget,
        })

    def _on_search_text_changed(self, text):
        self.search_timer.stop()
        if text.strip():
            self.search_timer.start()
        else:
            self._clear_flash()

    def _score_match(self, query: str, target: dict) -> float:
        candidates = [
            target.get("label_lower", ""),
            target.get("key_lower", ""),
            target.get("category_lower", ""),
            target.get("category_key_lower", ""),
            target.get("extra_lower", ""),
        ]

        best = 0.0
        for cand in candidates:
            if not cand:
                continue
            if query == cand:
                best = max(best, 1.0)
                continue
            if cand.startswith(query):
                best = max(best, 0.95)
                continue
            if query in cand:
                idx = cand.find(query)
                best = max(best, 0.85 + (1 - idx / max(len(cand), 1)) * 0.1)
                continue

            ratio = SequenceMatcher(None, query, cand).ratio()
            best = max(best, ratio * 0.8)

        return best

    def _perform_search(self):
        query = self.search_input.text().strip().lower()
        if not query:
            return

        best_target = None
        best_score = 0.0

        for target in self.search_targets:
            score = self._score_match(query, target)
            if score > best_score:
                best_score = score
                best_target = target

        if best_target and best_score >= 0.25:
            widget = best_target["widget"]
            self.scroll_area.ensureWidgetVisible(widget)
            self._flash_widget(widget)

    def _flash_widget(self, widget):
        if self._flashed_widget is widget:
            # Already flashed; just restart the timer.
            self._flash_reset_timer.start()
            return

        if self._flashed_widget:
            self._flashed_widget.setStyleSheet(self._flashed_original_style)
            self._flashed_widget.setGraphicsEffect(self._flashed_original_effect)

        self._flashed_widget = widget
        self._flashed_original_style = widget.styleSheet()
        self._flashed_original_effect = widget.graphicsEffect()

        tint_bg = "rgba(88, 149, 252, 0.10)"
        widget.setStyleSheet(
            self._flashed_original_style +
            f"\nbackground-color: {tint_bg};"
            f"\nborder: 2px solid {BrandColors.ACCENT};"
            "\nborder-radius: 6px;"
        )

        effect = QGraphicsColorizeEffect()
        effect.setColor(QColor(BrandColors.ACCENT))
        effect.setStrength(0.15)
        widget.setGraphicsEffect(effect)
        self._flash_reset_timer.start()

    def _clear_flash(self):
        if self._flashed_widget:
            self._flashed_widget.setStyleSheet(self._flashed_original_style)
            self._flashed_widget.setGraphicsEffect(self._flashed_original_effect)
        self._flashed_widget = None
        self._flashed_original_style = ""
        self._flashed_original_effect = None

    def _on_category_clicked(self, item):
        self.is_auto_scrolling = True
        category_name = item.text()
        widget = self.category_widgets.get(category_name)
        if widget:
            self.scroll_area.ensureWidgetVisible(widget)

            # Let's just use a timer to reset the flag to be safe against race conditions
            # I spent WAY too long trying to do this with signals alone
            QTimer.singleShot(100, lambda: setattr(self, 'is_auto_scrolling', False))

    def _on_scroll(self, value):
        if self.is_auto_scrolling:
            return

        # Check if we are at the very bottom
        v_bar = self.scroll_area.verticalScrollBar()
        if value >= v_bar.maximum() - 5: # Small buffer for float inaccuracies
            # Select the last category
            count = self.category_list.count()
            if count > 0:
                last_item = self.category_list.item(count - 1)
                if last_item != self.category_list.currentItem():
                    self.category_list.blockSignals(True)
                    self.category_list.setCurrentItem(last_item)
                    self.category_list.blockSignals(False)
            return

        # Find which category is currently visible
        # To do it, we'll check the vertical position of each category widget relative to the scroll area
        
        scroll_pos = value
        closest_category = None
        
        # We want the category that is at the top of the view
        # The scroll_content coordinates
        
        for name, widget in self.category_widgets.items():
            # Get widget position relative to scroll content
            widget_pos = widget.y()
            
            # If the widget is above the scroll position (or slightly below), it's a candidate.
            # The last category whose Y position is <= scroll_pos + buffer is the active one.
            
            if widget_pos <= scroll_pos + 50: # 50px buffer
                closest_category = name
            else:
                # Since they are ordered, once we find one that is further down, we can stop
                pass
        
        # If we found a category, select it
        if closest_category:
            # Find the item in the list
            items = self.category_list.findItems(closest_category, Qt.MatchExactly)
            if items:
                item = items[0]
                if item != self.category_list.currentItem():
                    self.category_list.blockSignals(True)
                    self.category_list.setCurrentItem(item)
                    self.category_list.blockSignals(False)

    def _on_preset_changed(self, text):
        template_widget = self.field_widgets.get("formatting.formatting_template")
        if not template_widget:
            return

        if text == "Custom":
            template_widget.setEnabled(True)
            # We need to store the custom value temporarily if we switch away from Custom.
            
            if hasattr(self, "_last_custom_template"):
                # Ignoring lint because we know it exists here
                template_widget.setPlainText(self._last_custom_template)
                
        else:
            # If the widget is enabled, it means we are on Custom (or just started).
            if template_widget.isEnabled():
                self._last_custom_template = template_widget.toPlainText()
            
            template_widget.setEnabled(False)
            template_widget.setEnabled(False)
            if text == "Classic - Name":
                template_widget.setPlainText("{{name}}: {{content}}")
            elif text == "Classic - Role":
                template_widget.setPlainText("{{role}}: {{content}}")
            elif text == "XML-Like - Name":
                template_widget.setPlainText("<{{name}}>{{content}}</{{name}}>")
            elif text == "XML-Like - Role":
                template_widget.setPlainText("<{{role}}>{{content}}</{{role}}>")
            elif text == "Divided - Name":
                template_widget.setPlainText("### {{name}}\n{{content}}")
            elif text == "Divided - Role":
                template_widget.setPlainText("### {{role}}\n{{content}}")

    def _reset_formatting(self):
        preset_widget = self.field_widgets.get("formatting.formatting_preset")
        if preset_widget:
            preset_widget.setCurrentText("Classic - Name")

    def _reset_injection(self):
        position_widget = self.field_widgets.get("formatting.injection_position")
        content_widget = self.field_widgets.get("formatting.injection_content")
        
        if position_widget:
            position_widget.setCurrentText("Before")
        
        if content_widget:
            content_widget.setPlainText("[Important Instructions]")

    def save_settings(self):
        validation_errors = []
        
        for category in SCHEMA:
            for field in self._iter_fields(category.fields):
                key = f"{category.key}.{field.key}"
                widget = self.field_widgets.get(key)
                
                if widget:
                    value = None
                    if field.type == SettingType.BOOLEAN:
                        value = widget.isChecked()
                    elif field.type == SettingType.STRING or field.type == SettingType.PASSWORD:
                        value = widget.text()
                    elif field.type == SettingType.INTEGER:
                        text_val = widget.text()
                        value = int(text_val) if text_val else 0
                    elif field.type == SettingType.TEXTAREA:
                        value = widget.toPlainText()
                    elif field.type == SettingType.DROPDOWN:
                        value = widget.currentText()
                    elif field.type in [SettingType.BUTTON, SettingType.DIVIDER, SettingType.DESCRIPTION, SettingType.ROW]:
                        continue # These don't have values to save
                        
                    # Check dependencies
                    is_enabled = True
                    if field.depends:
                        dep_widget = self.field_widgets.get(field.depends)
                        if dep_widget:
                            if isinstance(dep_widget, Tumbler):
                                is_enabled = dep_widget.isChecked()
                            elif isinstance(dep_widget, StyledLineEdit) or isinstance(dep_widget, QLineEdit):
                                is_enabled = bool(dep_widget.text())
                            elif isinstance(dep_widget, StyledComboBox):
                                is_enabled = bool(dep_widget.currentText())
                        
                    if is_enabled:
                        # Check required
                        if field.required and not value:
                            if isinstance(widget, StyledLineEdit):
                                widget.set_error(True)
                            validation_errors.append(f"{field.label}: This field is required.")
                        
                        # Run validator if exists
                        elif field.validator:
                            try:
                                field.validator(value)
                                if isinstance(widget, StyledLineEdit):
                                    widget.set_error(False)
                            except ValueError as e:
                                if isinstance(widget, StyledLineEdit):
                                    widget.set_error(True)
                                validation_errors.append(f"{field.label}: {str(e)}")
                    else:
                        # If disabled, ensure no error state
                        if isinstance(widget, StyledLineEdit):
                            widget.set_error(False)
                    
                    if not validation_errors:
                        self.config_manager.set_setting(category.key, field.key, value)
        
        if validation_errors:
            error_msg = "\n".join(validation_errors)
            QMessageBox.warning(self, "Validation Error", f"Please fix the following errors:\n\n{error_msg}")
            return

        self.config_manager.save_settings()
        self.unsaved_changes = False
        self.settings_saved.emit()
        self.close()

    def closeEvent(self, event):
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to discard them?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
