import json
import os
from pathlib import Path
from typing import Any, Dict, List

"""Test data loading utilities."""


class TestDataLoader:
    """Utility class for loading test data."""

    @staticmethod
    def load_test_data():
        """Load test data for integration tests."""
        return {"test_key": "test_value"}

    def __init__(self, fixtures_dir: str = None):
        if fixtures_dir is None:
            fixtures_dir = os.path.join(os.path.dirname(__file__), "../fixtures")
        self.fixtures_dir = Path(fixtures_dir)

    def load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON test data from fixtures directory."""
        file_path = self.fixtures_dir / "data" / filename
        with open(file_path, "r") as f:
            return json.load(f)

    def load_devices(self) -> List[Dict[str, Any]]:
        """Load device test data."""
        data = self.load_json("devices.json")
        return data["devices"]

    def load_logs(self) -> List[Dict[str, Any]]:
        """Load log test data."""
        data = self.load_json("logs.json")
        return data["logs"]

    def load_rules(self) -> List[Dict[str, Any]]:
        """Load rule test data."""
        data = self.load_json("rules.json")
        return data["rules"]

    def get_test_device(self, device_id: int = 1) -> Dict[str, Any]:
        """Get a specific test device by ID."""
        devices = self.load_devices()
        return next((d for d in devices if d["id"] == device_id), None)

    def get_test_logs_for_device(self, device_id: int) -> List[Dict[str, Any]]:
        """Get all test logs for a specific device."""
        logs = self.load_logs()
        return [log for log in logs if log["device_id"] == device_id]
