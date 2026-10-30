import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def load_script(filename):
    """Import a script whose name isn't a valid module name (e.g. 01_split_large_csv.py)."""
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
