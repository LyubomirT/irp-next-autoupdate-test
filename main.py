import sys
import asyncio
import uvicorn
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Slot
import qasync

from deepseek_driver import DeepSeekDriver
from api import API

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IntenseRP Next v2 (indev)")
        self.resize(300, 150)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.status_label = QLabel("Ready")
        self.layout.addWidget(self.status_label)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.on_start_clicked)
        self.layout.addWidget(self.start_button)

        self.driver = None
        self.api = None
        self.server = None

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
            self.driver = DeepSeekDriver()
            self.api = API(self.driver)
            
            # Configure Uvicorn
            config = uvicorn.Config(app=self.api.app, host="127.0.0.1", port=8000, log_level="info")
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
            self.start_button.setEnabled(True)
            
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
            self.start_button.setEnabled(True)
            self.start_button.setText("Start")
            print(f"Error starting services: {e}")

    async def stop_services(self):
        print("Stopping services...")
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
            self.start_button.setEnabled(True)
            print("Services stopped.")
        except Exception as e:
            print(f"Error stopping services: {e}")
            self.status_label.setText(f"Error stopping: {e}")
            self.start_button.setEnabled(True)

    def closeEvent(self, event):
        # Cleanup on close
        print("Window closing, shutting down...")
        # qasync loop runs until the window closes usually, but we need to await the cleanup.
        
        if self.status_label.text() == "Stopped" or self.status_label.text() == "Ready":
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
            self.close()
            
        asyncio.create_task(cleanup_and_close())

def main():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
