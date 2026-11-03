"""Configuration management and agent settings loader."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class AgentModelConfig(BaseModel):
    """Configuration parameters for a specific agent model."""

    model: str = Field(default="gemini-2.5-flash", description="Model name or identifier")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0, description="Sampling temperature")
    seed: int | None = Field(default=42, description="Random seed for reproducibility")
    thinking_budget: int | None = Field(default=0, ge=0, description="Thinking budget tokens")


class AppConfig(BaseModel):
    """Application-wide configuration containing agent configs."""

    default: AgentModelConfig = Field(default_factory=AgentModelConfig)
    agents: dict[str, AgentModelConfig] = Field(default_factory=dict)


class ConfigManager:
    """Loads and resolves agent configurations from YAML and environment overrides."""

    def __init__(self, config_path: str | Path | None = None):
        self.config_path = self._resolve_config_path(config_path)
        self.config = self._load_config()

    @staticmethod
    def _resolve_config_path(explicit_path: str | Path | None) -> Path | None:
        if explicit_path:
            p = Path(explicit_path)
            if p.exists():
                return p
        env_path = os.environ.get("AGENTIC_CONFIG_PATH")
        if env_path:
            p = Path(env_path)
            if p.exists():
                return p
        # Check standard default locations
        candidates = [
            Path("config/agents.yaml"),
            Path(__file__).parent.parent.parent / "config" / "agents.yaml",
            Path.home() / ".config" / "agentic" / "agents.yaml",
        ]
        for c in candidates:
            if c.exists():
                return c.resolve()
        return None

    def _load_config(self) -> AppConfig:
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    raw_data = yaml.safe_load(f) or {}
                return AppConfig.model_validate(raw_data)
            except Exception:
                pass
        return AppConfig()

    def get_agent_config(self, agent_name: str) -> AgentModelConfig:
        """Retrieve model configuration for an agent with fallback to default."""
        # Check environment variable overrides first
        env_model_key = f"AGENTIC_{agent_name.upper()}_MODEL"
        env_model = os.environ.get(env_model_key) or os.environ.get("AGENTIC_MODEL")

        if agent_name in self.config.agents:
            cfg = self.config.agents[agent_name].model_copy()
        else:
            cfg = self.config.default.model_copy()

        if env_model:
            cfg.model = env_model
        return cfg
