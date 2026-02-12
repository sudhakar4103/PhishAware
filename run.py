#!/usr/bin/env python
"""
PhishAware Application Entry Point

Run the Flask application server.
Usage: python run.py
"""

import os
import sys
import logging
from werkzeug.security import generate_password_hash

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from database.models import Admin

logger = logging.getLogger(__name__)

# Create application instance
app = create_app()


def init_db():
    """Initialize database and create default admin user."""
    with app.app_context():
        db.create_all()
        
        # Create default admin user if it doesn't exist
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(
                username='admin',
                email='admin@phishaware.local',
                full_name='Administrator',
                password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            logger.info('Default admin user created: admin / admin123')


@app.shell_context_processor
def make_shell_context():
    """Flask shell context."""
    from database.models import Campaign, Employee, CampaignEmployee
    return {
        'db': db,
        'Admin': Admin,
        'Campaign': Campaign,
        'Employee': Employee,
        'CampaignEmployee': CampaignEmployee
    }


if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run application
    print("=" * 60)
    print("🎯 PhishAware - Phishing Awareness Training Platform")
    print("=" * 60)
    print(f"🌐 Server starting at: http://localhost:5000")
    print(f"📝 Default login: admin / admin123")
    print(f"⚠️  Change default credentials in production!")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
