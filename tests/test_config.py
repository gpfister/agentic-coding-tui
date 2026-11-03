"""Unit tests for configuration loading and resolution."""

from pathlib import Path

from agentic_code_tui.config import AgentModelConfig, ConfigManager


def test_agent_model_config_defaults():
    cfg = AgentModelConfig()
    assert cfg.model == "gemini-2.5-flash"
    assert cfg.temperature == 0.2
    assert cfg.seed == 42
    assert cfg.thinking_budget == 0


def test_config_manager_load_yaml(tmp_path: Path):
    yaml_content = """
default:
  model: "gemini-2.5-flash"
  temperature: 0.2
agents:
  custom_agent:
    model: "gemini-3.8-pro"
    temperature: 0.1
    seed: 99
"""
    cfg_file = tmp_path / "agents.yaml"
    cfg_file.write_text(yaml_content, encoding="utf-8")

    cm = ConfigManager(config_path=cfg_file)
    assert cm.config_path == cfg_file

    custom_cfg = cm.get_agent_config("custom_agent")
    assert custom_cfg.model == "gemini-3.8-pro"
    assert custom_cfg.temperature == 0.1
    assert custom_cfg.seed == 99

    default_cfg = cm.get_agent_config("nonexistent_agent")
    assert default_cfg.model == "gemini-2.5-flash"
    assert default_cfg.temperature == 0.2


def test_config_manager_env_override(monkeypatch):
    monkeypatch.setenv("AGENTIC_CODING_ORCHESTRATOR_MODEL", "custom-model-override")
    cm = ConfigManager()
    cfg = cm.get_agent_config("coding_orchestrator")
    assert cfg.model == "custom-model-override"
