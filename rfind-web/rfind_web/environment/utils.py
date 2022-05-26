import warnings
from pathlib import Path

from .defaults import (
    DEFAULT_DATA_VARS,
    DEFAULT_S3_VARS,
    DEFAULT_SIM_VARS,
    DEFAULT_SOCKETIO_VARS,
)


def get_env_dir() -> Path:
    """
    Get the directory of the .env file
    """
    return Path(__file__).parent.parent.parent


def get_env_files() -> list:
    """
    Get the list of environment files
    """
    env_dir = get_env_dir()
    env_files = env_dir.glob("**.env**")
    return list(env_files)


def load_env() -> dict:
    """
    Load environment variables from .env file
    """
    env_dir = get_env_dir()

    try:
        env = file_to_dict(env_dir / ".env.local")
    except FileNotFoundError:
        warnings.warn(
            "No .env.local file found in {}. Defaulting to"
            " rfind_web.environment.defaults".format(env_dir)
        )
        env = get_all_defaults()

    return env


def file_to_dict(p: Path) -> dict:
    """
    Convert a env formatted file to a dictionary.
    TODO could be replaced with python-dotenv package
    """
    env = {}
    with open(p) as f:
        for line in f:
            if line.startswith("#"):
                continue
            key, val = line.split("=")
            env[key] = val.strip()
    return env


def get_all_defaults() -> dict:
    """
    Get the default values for all environment variables
    """
    return {
        **DEFAULT_SOCKETIO_VARS,
        **DEFAULT_DATA_VARS,
        **DEFAULT_S3_VARS,
        **DEFAULT_SIM_VARS,
    }
