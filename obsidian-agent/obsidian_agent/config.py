import json, os
from pathlib import Path

REQUIRED = ["vault_path", "daily_notes_folder", "output_folder", "model", "anthropic_api_key_env"]

class ConfigError(Exception):
    pass

def load_config(path: str) -> dict:
    with open(path) as f:
        cfg = json.load(f)
    for k in REQUIRED:
        if k not in cfg:
            raise ConfigError(f"missing required key: {k}")
    for k in ["vault_path", "website_repo_local"]:
        if k in cfg:
            cfg[k] = str(Path(cfg[k]).expanduser())
    return cfg
