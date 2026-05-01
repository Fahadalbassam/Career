"""
conftest.py – pytest configuration for the career-finder-ai test suite.

Adds the backend directory to sys.path so that `app.*` imports work
when running pytest from the project root or the backend directory.
"""

import sys
from pathlib import Path

# Ensure the backend directory is on the Python path
backend_dir = Path(__file__).parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
