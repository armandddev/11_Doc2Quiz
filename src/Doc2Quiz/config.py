from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import yaml

# Lecture du YAML
_yaml_path = Path(__file__).parent.parent.parent / "config.yaml"
_yaml_cfg = yaml.safe_load(_yaml_path.read_text(encoding="utf-8")) if _yaml_path.exists() else {}
_av = _yaml_cfg.get("anti_verbatim", {})

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    anti_verbatim_threshold: float = _av.get("threshold", 0.40)
    anti_verbatim_max_retries: int = _av.get("max_retries", 2)

settings = Settings()