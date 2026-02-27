# tests/test_config.py
import json, pytest
from obsidian_agent.config import load_config, ConfigError

def test_load_valid_config(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({
        "vault_path": str(tmp_path), "daily_notes_folder": "Daily Notes",
        "output_folder": "Zettelkasten", "model": "claude-sonnet-4-6",
        "anthropic_api_key_env": "ANTHROPIC_API_KEY"
    }))
    assert load_config(str(cfg))["model"] == "claude-sonnet-4-6"

def test_missing_key_raises(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"vault_path": "/tmp"}))
    with pytest.raises(ConfigError, match="missing required key"):
        load_config(str(cfg))

def test_tilde_expanded(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({
        "vault_path": "~/some/path", "daily_notes_folder": "Daily Notes",
        "output_folder": "Zettelkasten", "model": "claude-sonnet-4-6",
        "anthropic_api_key_env": "ANTHROPIC_API_KEY"
    }))
    assert not load_config(str(cfg))["vault_path"].startswith("~")
