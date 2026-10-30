"""Default simulation resources are resolved from the installed package."""
import json
from importlib.resources import files
from pathlib import Path


def load_json_resource(kind: str, name: str) -> dict:
    return json.loads(files("eaon_gov").joinpath("data", kind, name).read_text(encoding="utf-8"))


def load_json_path(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
