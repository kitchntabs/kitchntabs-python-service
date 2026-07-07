#!/usr/bin/env python3
"""
KitchnTabs System Tray Application
Monitors kt_service status and provides system tray icon + overlay UI
"""

import sys
import json
import os
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QDialog, QCheckBox, QPushButton, QSystemTrayIcon, QMenu
)
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QFont
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QObject, QThread
import pystray
from PIL import Image, ImageDraw

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StatusSignals(QObject):
    """Signals for status updates"""
    status_changed = pyqtSignal(dict)


class StatusMonitor(QThread):
    """Background thread that monitors status file"""

    def __init__(self, status_file: Path):
        super().__init__()
        self.status_file = status_file
        self.signals = StatusSignals()
        self.running = True
        self.last_status = None

    def run(self):
        """Monitor status file for changes"""
        while self.running:
            try:
                if self.status_file.exists():
                    with open(self.status_file, 'r') as f:
                        status = json.load(f)

                    # Only emit if status changed
                    if status != self.last_status:
                        self.signals.status_changed.emit(status)
                        self.last_status = status
            except Exception as e:
                logger.warning(f"Error reading status file: {e}")

            time.sleep(1)  # Check every second

    def stop(self):
        """Stop monitoring"""
        self.running = False


class StatusOverlay(QWidget):
    """Transparent overlay window showing kt_service status"""

    def __init__(self):
        super().__init__()
        self.current_status = None
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        # Make window transparent and always on top
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")

        # Position at top-right corner
        self.setGeometry(100, 100, 320, 140)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Status label
        self.label = QLabel("Status: Initializing...")
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 180);
                padding: 12px;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        self.label.setMinimumWidth(300)
        self.label.setWordWrap(True)

        layout.addWidget(self.label)
        self.setLayout(layout)

    def update_status(self, status: Dict[str, Any]):
        """Update displayed status"""
        self.current_status = status

        if not status:
            self.label.setText("⚠ kt_service not running")
            return

        state = status.get('state', {})
        metrics = status.get('metrics', {})
        connected = state.get('connected', False)

        # Build status text
        lines = []
        lines.append(f"{'✓' if connected else '✗'} Connected: {connected}")
        lines.append(f"⏱ Uptime: {state.get('uptime_seconds', 0)}s")
        lines.append(f"📨 Messages: {metrics.get('messages_received', 0)}")
        lines.append(f"🖨️  Prints: {metrics.get('print_jobs_processed', 0)}")
        lines.append(f"🔊 TTS: {metrics.get('tts_jobs_processed', 0)}")

        error = state.get('last_error')
        if error:
            lines.append(f"❌ Error: {error}")

        self.label.setText('\n'.join(lines))


class SettingsDialog(QDialog):
    """Settings dialog for tray configuration"""

    def __init__(self, settings: Dict[str, bool], parent=None):
        super().__init__(parent)
        self.settings = settings
        self.init_ui()

    def init_ui(self):
        """Initialize settings UI"""
        self.setWindowTitle("KitchnTabs Service Settings")
        self.setGeometry(200, 200, 400, 250)

        layout = QVBoxLayout()

        # Settings checkboxes
        self.tts_checkbox = QCheckBox("Enable Text-to-Speech (TTS)")
        self.tts_checkbox.setChecked(self.settings.get('tts_enabled', True))
        layout.addWidget(self.tts_checkbox)

        self.print_checkbox = QCheckBox("Enable Printing")
        self.print_checkbox.setChecked(self.settings.get('print_enabled', True))
        layout.addWidget(self.print_checkbox)

        self.notify_checkbox = QCheckBox("Enable Notifications")
        self.notify_checkbox.setChecked(self.settings.get('notifications_enabled', True))
        layout.addWidget(self.notify_checkbox)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_settings(self) -> Dict[str, bool]:
        """Get updated settings"""
        return {
            'tts_enabled': self.tts_checkbox.isChecked(),
            'print_enabled': self.print_checkbox.isChecked(),
            'notifications_enabled': self.notify_checkbox.isChecked(),
        }


class KtStatusTray:
    """Main system tray application"""

    def __init__(self):
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication(sys.argv)

        self.app.setQuitOnLastWindowClosed(False)

        # Status file
        self.status_file = self._get_status_file_path()

        # Settings
        self.settings = {
            'tts_enabled': True,
            'print_enabled': True,
            'notifications_enabled': True,
        }

        # Create overlay
        self.overlay = StatusOverlay()
        self.overlay.show()

        # Setup tray icon
        self.tray = QSystemTrayIcon()
        self.create_tray_icon()
        self.tray.show()

        # Status monitor thread
        self.monitor = StatusMonitor(self.status_file)
        self.monitor.signals.status_changed.connect(self.on_status_changed)
        self.monitor.start()

        logger.info("KitchnTabs System Tray started")

    @staticmethod
    def _get_status_file_path() -> Path:
        """Get status file path"""
        if os.name == 'nt':  # Windows
            status_dir = Path.home() / 'AppData' / 'Local' / 'kitchntabs' / '.kt_service'
        else:  # Unix/Linux/macOS
            status_dir = Path.home() / '.kt_service'

        return status_dir / 'status.json'

    def create_tray_icon(self):
        """Create tray icon and menu"""
        # Create icon
        icon = self.create_icon(connected=False)
        self.tray.setIcon(icon)
        self.tray.setToolTip("KitchnTabs Service")

        # Create menu
        menu = QMenu()

        show_action = menu.addAction("Show Status")
        show_action.triggered.connect(self.show_overlay)

        hide_action = menu.addAction("Hide Status")
        hide_action.triggered.connect(self.hide_overlay)

        menu.addSeparator()

        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self.show_settings)

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_app)

        self.tray.setContextMenu(menu)

    @staticmethod
    def create_icon(connected: bool = False, size: int = 64) -> QIcon:
        """Create tray icon (green if connected, red if not)"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        # Draw circle
        color = QColor("#7faa00") if connected else QColor("#ff6b6b")  # Green or red
        painter.setBrush(color)
        painter.drawEllipse(10, 10, size - 20, size - 20)

        # Draw center dot
        painter.setBrush(QColor("white"))
        painter.drawEllipse(size // 2 - 5, size // 2 - 5, 10, 10)

        painter.end()

        return QIcon(pixmap)

    def on_status_changed(self, status: Dict[str, Any]):
        """Handle status update"""
        connected = status.get('state', {}).get('connected', False)
        self.tray.setIcon(self.create_icon(connected=connected))
        self.overlay.update_status(status)

    def show_overlay(self):
        """Show overlay window"""
        self.overlay.show()

    def hide_overlay(self):
        """Hide overlay window"""
        self.overlay.hide()

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.settings, self.overlay)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.get_settings()
            logger.info(f"Settings updated: {self.settings}")
            # TODO: Write settings to config file

    def quit_app(self):
        """Quit application"""
        self.monitor.stop()
        self.monitor.wait()
        self.app.quit()

    def run(self):
        """Run the application"""
        sys.exit(self.app.exec())


if __name__ == '__main__':
    tray = KtStatusTray()
    tray.run()
