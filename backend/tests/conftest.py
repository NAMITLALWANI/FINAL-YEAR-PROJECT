from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BACKEND_DIR / 'scripts'
ROOT_DIR = BACKEND_DIR.parent

for d in [BACKEND_DIR, SCRIPTS_DIR, ROOT_DIR]:
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))
