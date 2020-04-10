import json
import yaml
from pathlib import Path


def load_yaml(f: Path) -> dict:
    with f.open("r") as fd:
        return yaml.safe_load(fd)


def load_json(f: Path) -> dict:
    with f.open("r") as fd:
        return json.load(fd)


def load_any(f: Path) -> dict:
    ext = f.suffix[1:]
    if ext in ["yml", "yaml"]:
        return load_yaml(f)
    elif ext in ["json"]:
        return load_json(f)
    else:
        raise Exception("Unsupported extension")


SUPPORTED_EXTENSIONS = ["yml", "yaml", "json"]
