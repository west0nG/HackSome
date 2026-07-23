"""Ensure the repo root is importable as `orchestration` regardless of how
pytest is invoked (mirrors agent/tests/conftest.py)."""

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
