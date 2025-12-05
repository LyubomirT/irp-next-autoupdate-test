import sys
import asyncio
import uvicorn
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import Slot, Qt
import qasync

from deepseek_driver import DeepSeekDriver
from api import API
from config.manager import ConfigManager
from ui.settings_window import SettingsWindow
from ui.console_window import ConsoleWindow
from ui.brand import BrandColors
from ui.icons import IconUtils, IconType
from utils.logger import Logger, LogLevel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IntenseRP Next v2 (indev)")
        self.resize(350, 200)
        self.setStyleSheet(f"background-color: {BrandColors.WINDOW_BG}; color: {BrandColors.TEXT_PRIMARY};")

        self.config_manager = ConfigManager()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {BrandColors.TEXT_SECONDARY};")
        self.layout.addWidget(self.status_label)

        # Buttons Layout
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start")
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {BrandColors.ACCENT};
                color: {BrandColors.TEXT_PRIMARY};
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #4a80e0;
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
                padding: 10px;
                border-radius: 4px;
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
        
        # Initialize console based on settings
        self._setup_console()

    def _setup_console(self):
        """Setup console window based on settings."""
        enable_console = self.config_manager.get_setting("system_settings", "enable_console")
        if enable_console:
            self._show_console()
        else:
            self._hide_console()
    
    def _show_console(self):
        """Show the console window and connect logger."""
        if not self.console_window:
            self.console_window = ConsoleWindow(self.config_manager)
        
        # Set logger callback
        Logger.set_console_callback(self._on_log_message)
        
        self.console_window.show()
        Logger.info("Console initialized.")
    
    def _hide_console(self):
        """Hide the console window and disconnect logger."""
        Logger.set_console_callback(None)
        
        if self.console_window:
            self.console_window.force_close()
            self.console_window = None
    
    def _on_log_message(self, level: LogLevel, message: str):
        """Callback for logger to send messages to console."""
        if self.console_window:
            self.console_window.append_log(level.value, message)

    def open_settings(self):
        if not self.settings_window:
            # Pass None as parent to make it a top-level window with its own taskbar icon
            self.settings_window = SettingsWindow(self.config_manager, None)
            self.settings_window.settings_saved.connect(self.on_settings_saved)
        self.settings_window.show()
        self.settings_window.activateWindow() # Bring to front

    def on_settings_saved(self):
        Logger.info("Settings saved.")
        # Handle console toggle
        self._setup_console()
        
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
            self.status_label.setText("Starting...")
            # Schedule the start_services coroutine
            asyncio.create_task(self.start_services())
        else:
            self.start_button.setEnabled(False)
            self.status_label.setText("Stopping...")
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
            self.status_label.setText("Launching Browser...")
            await self.driver.start()
            
            # Start API Server
            self.status_label.setText("Starting API Server...")
            # We run server.serve() as a task because it blocks
            self.server_task = asyncio.create_task(self.server.serve())
            
            self.status_label.setText("Running (Port 8000)")
            self.start_button.setText("Stop")
            IconUtils.apply_icon(self.start_button, IconType.STOP, BrandColors.TEXT_PRIMARY)
            self.start_button.setEnabled(True)
            
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
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
                
            self.status_label.setText("Stopped")
            self.start_button.setText("Start")
            IconUtils.apply_icon(self.start_button, IconType.START, BrandColors.TEXT_PRIMARY)
            self.start_button.setEnabled(True)
            Logger.success("Services stopped.")
        except Exception as e:
            Logger.error(f"Error stopping services: {e}")
            self.status_label.setText(f"Error stopping: {e}")
            self.start_button.setEnabled(True)

    async def on_browser_crashed(self):
        """
        Callback for when the browser crashes or is closed manually.
        """
        Logger.warning("Browser crash callback received.")
        self.status_label.setText("Browser Closed/Crashed")
        
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
            self.status_label.setText(f"Error: {e}")
            self.start_button.setEnabled(True)

    def closeEvent(self, event):
        # Cleanup on close
        Logger.info("Window closing, shutting down...")
        # qasync loop runs until the window closes usually, but we need to await the cleanup.
        
        if self.status_label.text() in ["Stopped", "Ready", "Browser Closed/Crashed"]:
            # Close console window if open
            if self.console_window:
                self.console_window.force_close()
                self.console_window = None
            event.accept()
            return

        event.ignore()
        self.status_label.setText("Shutting down...")
        
        async def cleanup_and_close():
            await self.stop_services()
            # Now we can close
            # We need to call close again, but bypass this check
            # We can reset the status label
            self.status_label.setText("Stopped")
            
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