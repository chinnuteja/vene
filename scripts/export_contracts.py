import json
import argparse
from pathlib import Path
from bring_vene.main import create_app

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, default=root / "packages" / "contracts" / "openapi.json")
target = parser.parse_args().output
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(create_app().openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

