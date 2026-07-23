import os
import sys

# Put repo root on sys.path so `import orchestration` / `import peripheral` work
# regardless of cwd (mirrors orchestration/tests/conftest.py).
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
