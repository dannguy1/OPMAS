"""
OPMAS Core Package
"""

from .config import load_config, get_config
from .main import main

__all__ = ['load_config', 'get_config', 'main']
