"""Quick smoke tests for the GAE application."""

import os
import sys
import unittest
from pathlib import Path

from flask.testing import FlaskClient


# Disable OpenTelemetry exporters during testing
os.environ["OTEL_SDK_DISABLED"] = "true"

# Ensure 'main' directory is in sys.path
MAIN_DIR = str(Path(__file__).resolve().parent.parent / "main")
if MAIN_DIR not in sys.path:
    sys.path.insert(0, MAIN_DIR)

from main import app  # noqa: E402


class AppTestCase(unittest.TestCase):
    """Test suite for core application routes."""

    client: FlaskClient

    def setUp(self) -> None:
        """Set up test client before each test."""
        app.testing = True
        self.client = app.test_client()

    def test_index_handler(self) -> None:
        """Verify the index page returns HTTP 200."""
        response = self.client.get("/")
        assert response.status_code == 200

    def test_non_existent_handler(self) -> None:
        """Verify a non-existent route returns HTTP 404."""
        response = self.client.get("/not-there")
        assert response.status_code == 404


if __name__ == "__main__":
    unittest.main()
