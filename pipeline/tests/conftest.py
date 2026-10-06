import sys
from pathlib import Path

# Add project root and pipeline dir to sys.path
root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "pipeline"))
