"""
API server for MultiAgenticSwarm.
"""

from fastapi import FastAPI
from ..web.app import create_app


def create_api(system) -> FastAPI:
    """Create API server (alias for web app)."""
    return create_app(system)
