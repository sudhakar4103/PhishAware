"""
PhishAware Application Factory
Version: 1.0.0
Date: February 12, 2026

Creates and configures the Flask application with blueprints and extensions.
"""
__version__ = '1.0.0'

import os
import logging
from flask import Flask, jsonify
from sqlalchemy import text

# Import extensions
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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
    # Initialize CSRF protection
    csrf = CSRFProtect(app)

    # Initialize rate limiter with sensible defaults
    limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["200/day", "50/hour"])
    
    # Initialize extensions with app
    db.init_app(app)
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)

    @app.route('/health', methods=['GET'])
    def health_check():
        try:
            db.session.execute(text('SELECT 1'))
            return jsonify(status='ok', database='ok'), 200
        except Exception as exc:
            app.logger.error('Health check failed: %s', exc)
            return jsonify(status='error', database='unavailable'), 503
    
    # Create database tables
    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
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

    # Backwards-compatible top-level aliases for legacy templates that use
    # `url_for('login')`, `url_for('logout')`, and root path.
    try:
        from app.routes.auth import index as auth_index, login as auth_login, logout as auth_logout
        from app.routes.admin import dashboard as admin_dashboard_view, click_statistics_report as click_statistics_view, quiz_analytics_report as quiz_analytics_view, awareness_report as awareness_view
        from app.routes.campaigns import campaigns_list as campaigns_list_view

        app.add_url_rule('/', endpoint='index', view_func=auth_index, methods=['GET'])
        app.add_url_rule('/login', endpoint='login', view_func=auth_login, methods=['GET', 'POST'])
        app.add_url_rule('/logout', endpoint='logout', view_func=auth_logout, methods=['POST'])

        # Aliases for legacy template endpoints
        app.add_url_rule('/admin/dashboard', endpoint='admin_dashboard', view_func=admin_dashboard_view, methods=['GET'])
        app.add_url_rule('/admin/campaigns', endpoint='campaigns_list', view_func=campaigns_list_view, methods=['GET'])
        # Campaign action aliases
        from app.routes.campaigns import create_campaign as create_campaign_view, campaign_detail as campaign_detail_view, add_employees_to_campaign as add_employees_view, send_campaign_emails as send_campaign_emails_view, test_email as test_email_view, edit_campaign as edit_campaign_view, resend_campaign as resend_campaign_view
        from app.routes.awareness import awareness_portal as awareness_portal_view, quiz_page as quiz_page_view, quiz_results as quiz_results_view
        app.add_url_rule('/admin/campaigns/create', endpoint='create_campaign', view_func=create_campaign_view, methods=['GET', 'POST'])
        app.add_url_rule('/admin/campaigns/<campaign_id>', endpoint='campaign_detail', view_func=campaign_detail_view, methods=['GET'])
        app.add_url_rule('/admin/campaigns/<campaign_id>/add-employees', endpoint='add_employees_to_campaign', view_func=add_employees_view, methods=['GET', 'POST'])
        app.add_url_rule('/admin/campaigns/<campaign_id>/edit', endpoint='edit_campaign', view_func=edit_campaign_view, methods=['GET', 'POST'])
        app.add_url_rule('/admin/campaigns/<campaign_id>/send-emails', endpoint='send_campaign_emails', view_func=send_campaign_emails_view, methods=['POST'])
        app.add_url_rule('/admin/campaigns/<campaign_id>/test-email', endpoint='test_email', view_func=test_email_view, methods=['POST'])
        app.add_url_rule('/admin/campaigns/<campaign_id>/resend', endpoint='resend_campaign', view_func=resend_campaign_view, methods=['GET', 'POST'])
        app.add_url_rule('/awareness/<campaign_id>/<tracking_token>', endpoint='awareness_portal', view_func=awareness_portal_view, methods=['GET'])
        app.add_url_rule('/quiz/<campaign_id>/<tracking_token>', endpoint='quiz_page', view_func=quiz_page_view, methods=['GET'])
        app.add_url_rule('/quiz/results/<tracking_token>', endpoint='quiz_results', view_func=quiz_results_view, methods=['GET'])
        app.add_url_rule('/admin/reports/click-statistics', endpoint='click_statistics_report', view_func=click_statistics_view, methods=['GET'])
        app.add_url_rule('/admin/reports/quiz-analytics', endpoint='quiz_analytics_report', view_func=quiz_analytics_view, methods=['GET'])
        app.add_url_rule('/admin/reports/awareness-report', endpoint='awareness_report', view_func=awareness_view, methods=['GET'])
    except Exception:
        # If import fails, skip adding aliases; blueprint routes should still work.
        pass


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
