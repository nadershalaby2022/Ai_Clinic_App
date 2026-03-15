import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
ROOT_APP = BASE_DIR / "app.py"

spec = importlib.util.spec_from_file_location("root_app", str(ROOT_APP))
root_app = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(root_app)

if __name__ == "__main__":
    root_app.main()
