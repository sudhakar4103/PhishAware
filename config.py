"""
Configuration management for PhishAware Training Platform.
Version: 1.0.0
Date: February 12, 2026

Handles environment variables and app configuration.
"""
__version__ = '1.0.0'

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


# Load environment variables from project .env for direct python execution.
PROJECT_ROOT = Path(__file__).resolve().parent

# Load a base .env first, then environment-specific overrides when available.
load_dotenv(PROJECT_ROOT / '.env')
current_env = os.getenv('FLASK_ENV', 'development').strip().lower()
if current_env == 'production':
    load_dotenv(PROJECT_ROOT / '.env.prod', override=True)
else:
    load_dotenv(PROJECT_ROOT / '.env.dev', override=True)

DEFAULT_SQLITE_DB_PATH = PROJECT_ROOT / 'instance' / 'phishaware.db'
DEFAULT_LOG_FILE_PATH = PROJECT_ROOT / 'logs' / 'phishaware.log'


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
        f'sqlite:///{DEFAULT_SQLITE_DB_PATH.as_posix()}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration (Gmail SMTP)
    GMAIL_USERNAME = os.getenv('GMAIL_USERNAME', '')
    GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', '')
    GMAIL_SMTP_HOST = os.getenv('GMAIL_SMTP_HOST', 'smtp.gmail.com')
    GMAIL_SMTP_PORT = int(os.getenv('GMAIL_SMTP_PORT', 587))

    # App configuration
    SENDER_EMAIL = os.getenv(
        'SENDER_EMAIL',
        os.getenv('GMAIL_USERNAME', 'phishing-simulator@demo-company.com')
    )
    SENDER_NAME = os.getenv('SENDER_NAME', 'Employee Training Portal')
    SERVER_URL = os.getenv('SERVER_URL', 'http://localhost:5000')
    TRUST_PROXY = os.getenv('TRUST_PROXY', 'False') == 'True'
    
    # Tracking and logging
    LOG_FILE = str(DEFAULT_LOG_FILE_PATH)
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

    @classmethod
    def validate(cls):
        """Raise at startup if required production environment variables are missing."""
        errors = []
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            errors.append("SECRET_KEY must be changed from the default value")
        if cls.SQLALCHEMY_DATABASE_URI == 'sqlite:///phishaware.db':
            errors.append("DATABASE_URL should use PostgreSQL or MySQL in production, not SQLite")
        if cls.SERVER_URL == 'http://localhost:5000':
            errors.append("SERVER_URL must be set to your public domain (e.g. https://yourdomain.com)")
        if errors:
            raise RuntimeError("Production config errors:\n" + "\n".join(f"  - {e}" for e in errors))


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
