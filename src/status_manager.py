"""
Status Manager for kt_service
Exports real-time status to JSON file for tray application monitoring
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class StatusManager:
    """Manages kt_service status export to shared status file"""

    def __init__(self):
        self.status_file = self._get_status_file_path()
        self.state = {
            'pid': os.getpid(),
            'connected': False,
            'uptime_seconds': 0,
            'websocket_url': '',
            'last_message_at': None,
            'connection_attempts': 0,
            'last_error': None,
        }
        self.metrics = {
            'messages_received': 0,
            'print_jobs_processed': 0,
            'tts_jobs_processed': 0,
            'errors': 0,
        }
        self.settings = {
            'tts_enabled': True,
            'print_enabled': True,
            'notifications_enabled': True,
            'log_level': 'INFO',
        }
        self.start_time = datetime.now()

    @staticmethod
    def _get_status_file_path() -> Path:
        """Get path to status file (~/.kt_service/status.json)"""
        if os.name == 'nt':  # Windows
            status_dir = Path.home() / 'AppData' / 'Local' / 'kitchntabs' / '.kt_service'
        else:  # Unix/Linux/macOS
            status_dir = Path.home() / '.kt_service'

        status_dir.mkdir(parents=True, exist_ok=True)
        return status_dir / 'status.json'

    def update_state(self, **kwargs) -> None:
        """Update state fields"""
        for key, value in kwargs.items():
            if key in self.state:
                self.state[key] = value

    def update_settings(self, **kwargs) -> None:
        """Update settings fields"""
        for key, value in kwargs.items():
            if key in self.settings:
                self.settings[key] = value

    def increment_metric(self, metric_name: str, amount: int = 1) -> None:
        """Increment a metric counter"""
        if metric_name in self.metrics:
            self.metrics[metric_name] += amount

    def record_error(self, error_msg: str) -> None:
        """Record an error"""
        self.state['last_error'] = error_msg
        self.increment_metric('errors')

    def export_status(self) -> None:
        """Export current status to JSON file"""
        try:
            # Calculate uptime
            uptime = (datetime.now() - self.start_time).total_seconds()
            self.state['uptime_seconds'] = int(uptime)

            status_data = {
                'pid': self.state['pid'],
                'timestamp': datetime.now().isoformat(),
                'state': self.state,
                'metrics': self.metrics,
                'settings': self.settings,
            }

            # Write to temp file first, then atomically rename (prevent corruption)
            temp_file = str(self.status_file) + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(status_data, f, indent=2)

            # Atomic rename
            os.replace(temp_file, str(self.status_file))
        except Exception as e:
            logger.warning(f"Failed to export status: {e}")
            # Don't raise - this shouldn't crash the service

    def load_settings(self, config_settings: Optional[Dict[str, Any]] = None) -> None:
        """Load settings from config"""
        if config_settings:
            for key, value in config_settings.items():
                if key in self.settings:
                    self.settings[key] = value

    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of current status for logging"""
        return {
            'connected': self.state['connected'],
            'uptime': f"{self.state['uptime_seconds']}s",
            'messages': self.metrics['messages_received'],
            'errors': self.metrics['errors'],
        }
