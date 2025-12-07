import sys
import asyncio
import uvicorn
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, 
    QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Slot, Qt
import qasync

from deepseek_driver import DeepSeekDriver
from api import API
from config.manager import ConfigManager
from ui.settings_window import SettingsWindow
from ui.console_window import ConsoleWindow
from ui.mini_console import MiniConsole
from ui.brand import BrandColors
from ui.icons import IconUtils, IconType
from utils.logger import Logger, LogLevel


def get_version():
    """Read version from version.txt file."""
    version_file = os.path.join(os.path.dirname(__file__), "version.txt")
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        version = get_version()
        self.setWindowTitle(f"IntenseRP Next v{version}")
        self.resize(450, 500)
        self.setStyleSheet(f"background-color: {BrandColors.WINDOW_BG}; color: {BrandColors.TEXT_PRIMARY};")

        self.config_manager = ConfigManager()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(12)

        # 1. Title Area
        title_label = QLabel(f"Welcome to IntenseRP Next (v{version})!")
        title_label.setStyleSheet(f"""
            font-size: {BrandColors.FONT_SIZE_TITLE};
            font-weight: bold;
            color: {BrandColors.TEXT_PRIMARY};
        """)
        title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title_label)

        # 1.5. Readiness Status
        self.status_label = QLabel("● Ready")
        self.status_label.setStyleSheet(f"""
            font-size: {BrandColors.FONT_SIZE_LARGE};
            font-weight: bold;
            color: {BrandColors.SUCCESS};
            padding: 8px;
            background-color: {BrandColors.SIDEBAR_BG};
            border-radius: 6px;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        # 2. Mini-Console Area
        self.mini_console = MiniConsole()
        self.mini_console.setMinimumHeight(250)
        self.mini_console.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.mini_console)

        # 3. Control Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.start_button = QPushButton("Start")
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {BrandColors.ACCENT};
                color: {BrandColors.TEXT_PRIMARY};
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: {BrandColors.FONT_SIZE_REGULAR};
            }}
            QPushButton:hover {{
                background-color: #4a80e0;
            }}
            QPushButton:disabled {{
                background-color: {BrandColors.TEXT_DISABLED};
            }}
        """)
        IconUtils.apply_icon(self.start_button, IconType.START, BrandColors.TEXT_PRIMARY)
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.clicked.connect(self.on_start_clicked)
        button_layout.addWidget(self.start_button)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {BrandColors.SIDEBAR_BG};
                color: {BrandColors.TEXT_PRIMARY};
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-size: {BrandColors.FONT_SIZE_REGULAR};
            }}
            QPushButton:hover {{
                background-color: {BrandColors.ITEM_HOVER};
            }}
        """)
        IconUtils.apply_icon(self.settings_button, IconType.SETTINGS, BrandColors.TEXT_PRIMARY)
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.clicked.connect(self.open_settings)
        button_layout.addWidget(self.settings_button)
        
        self.layout.addLayout(button_layout)

        self.driver = None
        self.api = None
        self.server = None
        self.settings_window = None
        self.console_window = None
        
        # Initialize logging based on settings
        self._setup_logging()
        
        # Always set the log callback for the mini-console
        Logger.set_console_callback(self._on_log_message)

    def _setup_logging(self):
        """Setup logging (console and file) based on settings."""
        # Console window (separate from mini-console)
        enable_console = self.config_manager.get_setting("system_settings", "enable_console")
        if enable_console:
            self._show_console()
        else:
            self._hide_console()
            
        # File Logging
        enable_files = self.config_manager.get_setting("logfiles", "enable_logfiles")
        log_dir = self.config_manager.get_setting("logfiles", "log_dir")
        max_files = self.config_manager.get_setting("logfiles", "max_files")
        max_size_val = self.config_manager.get_setting("logfiles", "size_val")
        size_unit = self.config_manager.get_setting("logfiles", "size_unit")
        
        # Defaults
        if log_dir is None: log_dir = "logs"
        if max_files is None: max_files = 5
        if max_size_val is None: max_size_val = 10
        if size_unit is None: size_unit = "MB"
        
        Logger.configure_file_logging(bool(enable_files), str(log_dir), int(max_files) if max_files is not None else 5, int(max_size_val) if max_size_val is not None else 10, str(size_unit))
    
    def _show_console(self):
        """Show the console window."""
        if not self.console_window:
            self.console_window = ConsoleWindow(self.config_manager)
        
        self.console_window.show()
        Logger.info("Console initialized.")
    
    def _hide_console(self):
        """Hide the console window."""
        if self.console_window:
            self.console_window.force_close()
            self.console_window = None
    
    def _on_log_message(self, level: LogLevel, message: str):
        """Callback for logger to send messages to console."""
        if self.console_window:
            self.console_window.append_log(level.value, message)
        
        # Also route to mini-console (always, except DEBUG which is filtered inside)
        self.mini_console.add_log(level, message)
    
    def _update_status(self, text: str, status_type: str = "info"):
        """Update the status label with appropriate styling."""
        color_map = {
            "ready": BrandColors.SUCCESS,
            "running": BrandColors.ACCENT,
            "warning": BrandColors.WARNING,
            "error": BrandColors.DANGER,
            "info": BrandColors.TEXT_SECONDARY,
        }
        color = color_map.get(status_type, BrandColors.TEXT_SECONDARY)
        
        # Add status indicator dot
        dot = "●" if status_type in ["ready", "running"] else "○"
        
        self.status_label.setText(f"{dot} {text}")
        self.status_label.setStyleSheet(f"""
            font-size: {BrandColors.FONT_SIZE_LARGE};
            font-weight: bold;
            color: {color};
            padding: 8px;
            background-color: {BrandColors.SIDEBAR_BG};
            border-radius: 6px;
        """)

    def open_settings(self):
        if not self.settings_window:
            # Pass None as parent to make it a top-level window with its own taskbar icon
            self.settings_window = SettingsWindow(self.config_manager, None)
            self.settings_window.settings_saved.connect(self.on_settings_saved)
        self.settings_window.show()
        self.settings_window.activateWindow() # Bring to front

    def on_settings_saved(self):
        Logger.info("Settings saved.")
        # Handle logging toggle
        self._setup_logging()
        
        # Update console settings if it exists
        # Rule 43 of The Internet: If it exists, then it exists
        if self.console_window:
            self.console_window.apply_settings()
            
        # If driver is running, it will pick up changes on next generation
        # All thanks to the config manager being dynamic

    @Slot()
    def on_start_clicked(self):
        if self.start_button.text() == "Start":
            self.start_button.setEnabled(False)
            self._update_status("Starting...", "info")
            # Schedule the start_services coroutine
            asyncio.create_task(self.start_services())
        else:
            self.start_button.setEnabled(False)
            self._update_status("Stopping...", "info")
            asyncio.create_task(self.stop_services())

    async def start_services(self):
        try:
            # Pass config manager to driver
            self.driver = DeepSeekDriver(self.config_manager)
            self.driver.on_crash_callback = self.on_browser_crashed
            
            self.api = API(self.driver)
            
            # Configure Uvicorn
            config = uvicorn.Config(app=self.api.app, host="127.0.0.1", port=7777, log_level="info")
            # 7777 for now because 8000 is used by SillyTavern
            self.server = uvicorn.Server(config)
            
            # Start Driver
            self._update_status("Launching Browser...", "info")
            await self.driver.start()
            
            # Start API Server
            self._update_status("Starting API Server...", "info")
            # We run server.serve() as a task because it blocks
            self.server_task = asyncio.create_task(self.server.serve())
            
            self._update_status("Running (Port 7777)", "running")
            self.start_button.setText("Stop")
            IconUtils.apply_icon(self.start_button, IconType.STOP, BrandColors.TEXT_PRIMARY)
            self.start_button.setEnabled(True)
            
        except Exception as e:
            self._update_status(f"Error: {e}", "error")
            self.start_button.setEnabled(True)
            self.start_button.setText("Start")
            IconUtils.apply_icon(self.start_button, IconType.START, BrandColors.TEXT_PRIMARY)
            Logger.error(f"Error starting services: {e}")

    async def stop_services(self):
        Logger.info("Stopping services...")
        try:
            if self.api:
                await self.api.stop()
                
            if self.server:
                self.server.should_exit = True
                if hasattr(self, 'server_task'):
                    await self.server_task
            
            if self.driver:
                await self.driver.close()
                
            self._update_status("Stopped", "ready")
            self.start_button.setText("Start")
            IconUtils.apply_icon(self.start_button, IconType.START, BrandColors.TEXT_PRIMARY)
            self.start_button.setEnabled(True)
            Logger.success("Services stopped.")
        except Exception as e:
            Logger.error(f"Error stopping services: {e}")
            self._update_status(f"Error stopping: {e}", "error")
            self.start_button.setEnabled(True)

    async def on_browser_crashed(self):
        """
        Callback for when the browser crashes or is closed manually.
        """
        Logger.warning("Browser crash callback received.")
        self._update_status("Browser Closed/Crashed", "warning")
        
        # We need to clean up all services including playwright
        try:
            if self.api:
                await self.api.stop()
                
            if self.server:
                self.server.should_exit = True
                if hasattr(self, 'server_task'):
                    await self.server_task
            
            # The driver's close() method handles None checks for context/browser, theoretically that is enough
            if self.driver:
                try:
                    await self.driver.close()
                except Exception as e:
                    Logger.error(f"Error closing driver after crash: {e}")
                self.driver = None
            
            # Reset UI
            self.start_button.setText("Start")
            IconUtils.apply_icon(self.start_button, IconType.START, BrandColors.TEXT_PRIMARY)
            self.start_button.setEnabled(True)
            
        except Exception as e:
            Logger.error(f"Error handling crash cleanup: {e}")
            self._update_status(f"Error: {e}", "error")
            self.start_button.setEnabled(True)

    def closeEvent(self, event):
        # Cleanup on close
        Logger.info("Window closing, shutting down...")
        # qasync loop runs until the window closes usually, but we need to await the cleanup.
        
        status_text = self.status_label.text()
        if any(state in status_text for state in ["Stopped", "Ready", "Browser Closed/Crashed"]):
            # Close console window if open
            if self.console_window:
                self.console_window.force_close()
                self.console_window = None
            event.accept()
            return

        event.ignore()
        self._update_status("Shutting down...", "info")
        
        async def cleanup_and_close():
            await self.stop_services()
            # Now we can close
            # We need to call close again, but bypass this check
            # We can reset the status label
            self._update_status("Stopped", "ready")
            
            # Close console window if open
            if self.console_window:
                self.console_window.force_close()
                self.console_window = None
            
            # Close settings window if open
            if self.settings_window:
                self.settings_window.close()
                
            self.close()
            
        asyncio.create_task(cleanup_and_close())

def main():
    app = QApplication(sys.argv)
    
    # Load Fonts
    from PySide6.QtGui import QFontDatabase, QFont
    import os
    
    font_dir = os.path.join(os.path.dirname(__file__), "ui", "fonts")
    if os.path.exists(font_dir):
        for filename in os.listdir(font_dir):
            if filename.endswith(".ttf"):
                QFontDatabase.addApplicationFont(os.path.join(font_dir, filename))
    
    # Set Global Font
    font = QFont(BrandColors.FONT_FAMILY)
    app.setFont(font)
    
    # Enforce Dark Mode Palette (or try to)
    app.setStyleSheet(f"""
        QWidget {{
            font-family: '{BrandColors.FONT_FAMILY}';
            background-color: {BrandColors.WINDOW_BG};
            color: {BrandColors.TEXT_PRIMARY};
        }}
    """)

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()