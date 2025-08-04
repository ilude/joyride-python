"""Joyride DNS Service Package."""
import os

# Don't import main here as it causes dependency issues in test environments
# Main app should be imported only when needed: from app.main import app

__version__ = os.getenv("SEMANTIC_VERSION", "dev")
