"""
PhishAware Application Factory
Version: 1.0.0
Date: February 12, 2026

Creates and configures the Flask application with blueprints and extensions.
"""
__version__ = '1.0.0'

import os
import logging
from flask import Flask

# Import db from existing database.models module
from database.models import db


def create_app(config_name=None):
    """
    Application factory function.
    
    Args:
        config_name: Configuration to use (development, production, testing)
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__,
                static_folder='../static',
                template_folder='../templates')
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    from config import get_config
    app.config.from_object(get_config())
    
    # Initialize extensions with app
    db.init_app(app)
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app


def register_blueprints(app):
    """Register all Flask blueprints."""
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.campaigns import campaigns_bp
    from app.routes.tracking import tracking_bp
    from app.routes.awareness import awareness_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(campaigns_bp, url_prefix='/admin/campaigns')
    app.register_blueprint(tracking_bp, url_prefix='/track')
    app.register_blueprint(awareness_bp)
    app.register_blueprint(api_bp, url_prefix='/api')


def register_error_handlers(app):
    """Register error handlers."""
    from flask import render_template
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', error='Page not found'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error='Internal server error'), 500


def setup_logging(app):
    """Configure application logging."""
    log_dir = os.path.dirname(app.config.get('LOG_FILE', 'logs/phishaware.log'))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(app.config['LOG_FILE']),
            logging.StreamHandler()
        ]
    )
