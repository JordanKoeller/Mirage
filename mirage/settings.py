"""
Module for loading settings.

Any dataclass that is compatible with the Dictify system can be used for settings.

All settings objects should be specified as separate entries in a yaml file. The
name of the key is controlled by the class name of the dataclass.
"""

import yaml
from functools import cache
import logging
import os
from pathlib import Path

from mirage.util import Dictify

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = str(Path.home() / ".config" / "mirage.yaml")

_CONFIG_PATH = os.getenv("MIRAGE_CONFIG_FILE", _DEFAULT_CONFIG_PATH)


@cache
def load_settings(settings_type: type) -> object:
  key = _settings_type_to_key(settings_type)
  if key not in _settings_dict():
    logger.debug(f"Settings for type {key} not found. Returning default settings.")
    return _default(settings_type)
  try:
    ret = Dictify.from_dict(settings_type, _settings_dict()[key])
    logger.debug("Returning settings: ", ret)
    return ret
  except ValueError:
    logger.warning(f"Could not parse settings of type {key}. Returning default settings.")
    return _default(settings_type)


def _default(settings_type: type) -> object:
  if hasattr(settings_type, "create_default"):
    return settings_type.create_default()
  return settings_type()


def _settings_type_to_key(settings_type: type) -> str:
  full_name = settings_type.__name__
  if "." in full_name:
    return full_name.split(".")[-1]
  else:
    return full_name


@cache
def _settings_dict() -> dict:
  try:
    with open(_CONFIG_PATH) as f:
      yaml_str = f.read()
      return yaml.load(yaml_str, yaml.CLoader)
  except EnvironmentError:
    logger.warning("Could not load custom configs. Using default configs.")
    return {}
