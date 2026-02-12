"""
Routes package initialization.
"""

from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.campaigns import campaigns_bp
from app.routes.tracking import tracking_bp
from app.routes.awareness import awareness_bp
from app.routes.api import api_bp

__all__ = ['auth_bp', 'admin_bp', 'campaigns_bp', 'tracking_bp', 'awareness_bp', 'api_bp']
