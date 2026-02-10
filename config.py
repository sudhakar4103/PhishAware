"""
Configuration management for PhishAware Training Platform.
Handles environment variables and app configuration.
"""

import os
from datetime import timedelta


class Config:
    """Base configuration for all environments."""
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True') == 'True'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///phishaware.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration (Mailtrap or SendGrid)
    EMAIL_PROVIDER = os.getenv('EMAIL_PROVIDER', 'mailtrap')  # 'mailtrap' or 'sendgrid'
    
    # Mailtrap Configuration
    MAILTRAP_USERNAME = os.getenv('MAILTRAP_USERNAME', '')
    MAILTRAP_PASSWORD = os.getenv('MAILTRAP_PASSWORD', '')
    MAILTRAP_HOST = os.getenv('MAILTRAP_HOST', 'mailtrap.io')
    MAILTRAP_PORT = int(os.getenv('MAILTRAP_PORT', 465))
    
    # SendGrid Configuration
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
    
    # App configuration
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'phishing-simulator@demo-company.com')
    SENDER_NAME = os.getenv('SENDER_NAME', 'Employee Training Portal')
    
    # Tracking and logging
    LOG_FILE = 'logs/phishaware.log'
    CLICK_TRACKING_TIMEOUT = 30  # days
    
    # Awareness portal settings
    QUIZ_TIME_LIMIT = 600  # seconds (10 minutes)
    QUIZ_PASS_SCORE = 70  # percentage
    
    # Risk scoring thresholds
    AWARENESS_LEVEL_HIGH = 80
    AWARENESS_LEVEL_MEDIUM = 50
    AWARENESS_LEVEL_LOW = 0


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    TESTING = False


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing environment configuration."""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False


# Dictionary for config selection
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV."""
    env = os.getenv('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)
