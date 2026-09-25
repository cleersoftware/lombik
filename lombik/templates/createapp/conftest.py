import sys
from pathlib import Path

# Make the generated app's packages (``application`` and ``models``) importable
# when pytest runs from the project root.
ROOT = Path(__file__).resolve().parent

sys.path.insert(0, str(ROOT))
