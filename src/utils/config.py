import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


# Load variables from .env if the file exists.
load_dotenv()


def load_config(config_path: str = "configs/config.yaml") -> dict:
    """
    Load application configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Configuration as a Python dictionary.
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return config or {}