"""Joyride DNS Service Package."""
import os

from .main import app  # noqa: F401

__version__ = os.getenv("SEMANTIC_VERSION", "dev")
