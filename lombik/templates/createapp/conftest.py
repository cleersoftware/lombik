import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[0]
TEMPLATE_ROOT = ROOT / "lombik" / "templates" / "createapp"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TEMPLATE_ROOT))