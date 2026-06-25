#!/usr/bin/env python
"""
Setup script for PhishAware Platform
Initializes database, creates admin user, and seeds sample data
"""

import os
import sys
from getpass import getpass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from database.models import Admin, Campaign, Employee
from werkzeug.security import generate_password_hash


def init_database():
    """Initialize database schema."""
    print("🔧 Initializing database...")
    with app.app_context():
        db.create_all()
        print("✓ Database schema created")


def create_admin_user():
    """Create admin user interactively."""
    print("\n👤 Creating Admin User")
    print("-" * 40)
    
    with app.app_context():
        # Check if admin exists
        if Admin.query.filter_by(username='admin').first():
            print("⚠️  Admin user 'admin' already exists")
            response = input("Delete and recreate? (y/n): ").lower()
            if response != 'y':
                return
            existing_admin = Admin.query.filter_by(username='admin').first()
            # Delete campaigns first to avoid foreign key constraint
            Campaign.query.filter_by(created_by_id=existing_admin.id).delete()
            db.session.delete(existing_admin)
            db.session.commit()
        
        username = input("Username (default: admin): ").strip() or "admin"
        email = input("Email: ").strip()
        full_name = input("Full Name: ").strip()
        
        password = getpass("Password: ")
        password_confirm = getpass("Confirm Password: ")
        
        if password != password_confirm:
            print("❌ Passwords do not match!")
            return
        
        # Create admin
        admin = Admin(
            username=username,
            email=email,
            full_name=full_name,
            password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
            is_active=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"✓ Admin user '{username}' created successfully")


def create_sample_campaign():
    """Create sample campaign for testing."""
    print("\n📧 Creating Sample Campaign")
    print("-" * 40)
    
    with app.app_context():
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            print("⚠️  Admin user not found. Create admin first.")
            return
        
        # Create sample campaign
        campaign = Campaign(
            campaign_id='sample-campaign-001',
            name='Sample Phishing Simulation',
            description='This is a sample campaign for testing',
            sender_name='IT Security Team',
            sender_email='security@fake-company.com',
            subject_line='Important: Please update your password',
            phishing_type='credential_harvesting',
            email_template='''
<p>Dear Employee,</p>

<p>We have detected suspicious activity on your account. Please update your password immediately 
by clicking the button below:</p>

<p><a href="https://update-account.fake-company.com/verify" style="background-color: #007bff; 
color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Update Password</a></p>

<p>Best regards,<br>
IT Security Team</p>
            ''',
            created_by_id=admin.id,
            status='draft'
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        print("✓ Sample campaign created")
        print(f"  Campaign ID: {campaign.campaign_id}")
        print(f"  You can now add employees and send the campaign")


def create_sample_employees():
    """Create sample employees for testing."""
    print("\n👥 Creating Sample Employees")
    print("-" * 40)
    
    sample_emails = [
        'john.doe@company.com',
        'jane.smith@company.com',
        'bob.wilson@company.com',
        'alice.johnson@company.com',
        'charlie.brown@company.com'
    ]
    
    with app.app_context():
        created_count = 0
        for email in sample_emails:
            if Employee.query.filter_by(email=email).first():
                print(f"⊘ {email} already exists, skipping...")
                continue
            
            employee = Employee(
                employee_id=f'emp-{created_count + 1}',
                email=email,
                full_name=email.split('@')[0].title().replace('.', ' '),
                department='Engineering'
            )
            db.session.add(employee)
            created_count += 1
        
        db.session.commit()
        print(f"✓ Created {created_count} sample employees")


def print_summary():
    """Print setup summary."""
    print("\n" + "=" * 50)
    print("✅ PhishAware Platform Setup Complete!")
    print("=" * 50)
    print("\n📋 Next Steps:")
    print("1. Run the application: python app.py")
    print("2. Access at: http://localhost:5000")
    print("3. Login with admin credentials")
    print("4. Create or view the sample campaign")
    print("5. Add employees and send phishing emails")
    print("\n⚠️  Security Reminders:")
    print("• Change default admin password in production")
    print("• Configure Gmail SMTP credentials")
    print("• Use HTTPS in production")
    print("• Set strong SECRET_KEY in .env")
    print("\n📚 Documentation: See README.md for details")
    print("=" * 50)


def main():
    """Main setup function."""
    print("\n" + "=" * 50)
    print("🎯 PhishAware Platform Setup")
    print("=" * 50)
    
    print("\n📦 Setting up PhishAware...")
    
    try:
        # Initialize database
        init_database()
        
        # Create admin user
        create_admin_user()
        
        # Ask about sample data
        response = input("\nCreate sample campaign and employees? (y/n): ").lower()
        if response == 'y':
            create_sample_campaign()
            create_sample_employees()
        
        # Print summary
        print_summary()
        
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
