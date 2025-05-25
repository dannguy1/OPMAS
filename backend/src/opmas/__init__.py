"""
OPMAS Core Package
"""

from .config import get_config, load_config
from .main import main

__all__ = ["load_config", "get_config", "main"]
