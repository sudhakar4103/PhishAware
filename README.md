# PhishAware - Phishing Awareness Training Platform

## 🎯 Overview

**PhishAware** is a production-ready, Python-based Phishing Awareness Training Platform designed for authorized employee security training. It allows administrators to send controlled phishing simulation emails, track user behavior, redirect users to educational content, conduct quizzes, and generate comprehensive awareness reports.

**⚠️ IMPORTANT:** This platform is designed **exclusively for authorized employee training**. It must only be used with explicit employee consent and in compliance with company policy and applicable laws.

## ✨ Key Features

### Admin Dashboard
- Create and manage phishing simulation campaigns
- Send controlled phishing emails to enrolled employees
- Real-time click tracking and statistics
- Comprehensive awareness reporting
- Department-level analysis
- Audit logging for compliance

### Employee Experience
- Click tracking with device/browser detection
- Phishing awareness portal with educational content
- Interactive quiz with auto-grading
- Detailed feedback on quiz performance
- No credential harvesting (no password capture)

### Security & Compliance
- Session-based admin authentication
- Role-based access control
- Complete audit trail
- GDPR-compliant data handling
- No sensitive data storage
- Unique tracking tokens per employee

## 📋 Technology Stack

- **Backend:** Python 3.8+, Flask 2.3+
- **Database:** SQLite (or PostgreSQL for production)
- **ORM:** SQLAlchemy
- **Email:** Mailtrap (testing) or SendGrid (production)
- **Authentication:** Session-based login
- **Frontend:** HTML5, Bootstrap 5, Chart.js
- **Security:** Werkzeug password hashing, HTTPS-ready

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Linux/macOS or Windows with WSL

### Step 1: Clone/Download Project
```bash
cd PhishAware
```

### Step 2: Create Virtual Environment
```bash
# On Linux/macOS
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create `.env` file in the project root:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-in-production

# Database
DATABASE_URL=sqlite:///phishaware.db

# Email (Mailtrap for testing)
EMAIL_PROVIDER=mailtrap
MAILTRAP_USERNAME=your-mailtrap-username
MAILTRAP_PASSWORD=your-mailtrap-password
MAILTRAP_HOST=live.mailtrap.io
MAILTRAP_PORT=465

# OR Email (SendGrid for production)
# EMAIL_PROVIDER=sendgrid
# SENDGRID_API_KEY=your-sendgrid-api-key

# Application Settings
SENDER_EMAIL=phishing-training@demo-company.com
SENDER_NAME=Security Training Team
SERVER_URL=http://localhost:5000
```

### Step 5: Initialize Database
```bash
# Start Python shell
python

# Inside Python shell
>>> from app import app, init_db
>>> init_db()
>>> exit()
```

### Step 6: Run Application
```bash
python app.py
```

Access the application at: **http://localhost:5000**

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

**⚠️ CHANGE THESE CREDENTIALS IN PRODUCTION!**

## 📖 Usage Guide

### Creating a Campaign

1. **Login** with admin credentials
2. **Dashboard** → Click "New Campaign"
3. **Configure:**
   - Campaign name
   - Phishing type (credential harvest, malware, urgent action)
   - Fake sender email (use dummy domain)
   - Subject line
   - Email body (HTML with phishing red flags)
4. **Add Employees:** Upload employee email list
5. **Send Emails:** Click "Send Emails" to launch campaign

### Monitoring Campaign

- **Real-time tracking** of clicks and opens
- **Quiz completion** monitoring
- **Risk scoring** per employee
- **Department analytics**

### Viewing Reports

1. **Click Statistics:** Which devices/browsers were used
2. **Quiz Analytics:** Pass rates, average scores
3. **Awareness Report:** Individual and department-level awareness

## 🏗️ Project Structure

```
PhishAware/
├── app.py                          # Main Flask application
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
│
├── database/
│   └── models.py                  # SQLAlchemy database models
│
├── email_service/
│   └── mailer.py                  # Email sending (Mailtrap/SendGrid)
│
├── tracking/
│   └── click_tracker.py           # Click event tracking
│
├── quiz/
│   └── quiz_engine.py             # Quiz questions and scoring
│
├── detection_engine/
│   └── risk_scoring.py            # Risk and awareness calculation
│
├── templates/
│   ├── base.html                  # Base template
│   ├── login.html                 # Admin login
│   ├── error.html                 # Error page
│   ├── admin/
│   │   ├── dashboard.html         # Admin dashboard
│   │   ├── campaigns.html         # Campaign list
│   │   ├── campaign_form.html     # Create campaign
│   │   ├── campaign_detail.html   # Campaign details
│   │   ├── add_employees.html     # Add employees
│   │   └── reports/
│   │       ├── click_statistics.html
│   │       ├── quiz_analytics.html
│   │       └── awareness_report.html
│   ├── awareness/
│   │   └── portal.html            # Phishing awareness content
│   └── quiz/
│       ├── quiz.html              # Quiz interface
│       └── results.html           # Quiz results
│
├── static/
│   ├── css/
│   │   └── style.css              # Application styling
│   └── js/
│       └── main.js                # JavaScript utilities
│
└── logs/
    └── phishaware.log             # Application log file
```

### Database Models

- **Admin:** Administrator users
- **Campaign:** Phishing simulation campaigns
- **Employee:** Training participants
- **CampaignEmployee:** Junction table for enrollment
- **ClickTracking:** Phishing link clicks
- **QuizResult:** Quiz performance
- **RiskScore:** Calculated awareness/risk metrics
- **AuditLog:** Security audit trail

## 🔒 Security Implementation

### Authentication & Authorization
- Session-based admin login with password hashing (PBKDF2)
- Admin-only dashboard access
- Public employee-facing portals (no auth needed to enter)

### Data Protection
- No credential/password capture
- Unique tracking tokens per employee (UUID v4)
- Click events include user agent but no sensitive data
- Database encryption recommended for production

### Email Security
- Fake sender addresses (never impersonate real company domain)
- Clear training disclaimers in emails
- No actual malware/phishing content delivery
- Password reset/authentication landing pages NOT used

### Tracking Privacy
- Click tracking IP addresses (informational only)
- Device/browser detection (non-PII)
- No personal data beyond email collected
- Audit log of all admin actions

## 📊 Risk Scoring Algorithm

Awareness is calculated as a weighted combination of:

**Overall Score = (Quiz Score × 0.4) + (Email Behavior Score × 0.6)**

### Email Behavior Score
- **Did not click:** 100 points
- **Clicked within 1 minute:** 30 points
- **Clicked within 5 minutes:** 55 points
- **Clicked within 30 minutes:** 80 points
- **Clicked within 60 minutes:** 85 points
- **Clicked after 60 minutes:** 90 points

### Awareness Levels
- **High:** Score ≥ 80
- **Medium:** Score 50-79
- **Low:** Score < 50

## 📧 Email Service Configuration

### Mailtrap (Testing)
1. Create Mailtrap account (free tier available)
2. Generate credentials
3. Add to `.env`:
   ```
   EMAIL_PROVIDER=mailtrap
   MAILTRAP_USERNAME=your_username
   MAILTRAP_PASSWORD=your_password
   ```

### SendGrid (Production)
1. Sign up for SendGrid
2. Generate API key
3. Add to `.env`:
   ```
   EMAIL_PROVIDER=sendgrid
   SENDGRID_API_KEY=your_api_key
   ```

## 🧪 Testing Workflow

1. **Create test account** in your email system
2. **Create campaign** with distinct phishing type
3. **Add test email** to campaign
4. **Send email** (will appear in inbox)
5. **Click link** in email
6. **Complete quiz** on awareness portal
7. **View results** in admin dashboard

## 🚨 Ethical Guidelines

### ✅ DO:
- Obtain explicit employee consent BEFORE campaigns
- Use clear training disclaimers
- Focus on education, not punishment
- Provide immediate feedback on results
- Support struggling employees with training
- Document compliance with company policy
- Report results to leadership

### ❌ DO NOT:
- Send without consent
- Use real company/brand domains
- Capture actual passwords
- Target employees for reputation
- Use results for disciplinary action without context
- Integrate with authentication systems
- Send to personal email addresses

## 🐛 Troubleshooting

### Emails Not Sending
- Check Mailtrap/SendGrid credentials in `.env`
- Verify email provider is running/responsive
- Check application logs: `tail -f logs/phishaware.log`
- Ensure sender email in `.env` matches provider configuration

### Database Errors
```bash
# Reset database
rm phishaware.db
python -c "from app import init_db; init_db()"
```

### Port Already in Use
```bash
# Run on different port
python -c "from app import app; app.run(port=5001)"
```

### Template Not Found Errors
- Verify all template files exist in `templates/` directory
- Check template folder structure matches code references
- Clear Flask cache: `rm -rf __pycache__`

## 📦 Production Deployment

### Pre-Deployment Checklist
- [ ] Change default admin password
- [ ] Set `FLASK_ENV=production`
- [ ] Set `SESSION_COOKIE_SECURE=True`
- [ ] Use PostgreSQL database (not SQLite)
- [ ] Use SendGrid or similar for email
- [ ] Enable HTTPS/TLS
- [ ] Set strong `SECRET_KEY`
- [ ] Review all admin accounts
- [ ] Test email configuration
- [ ] Backup database regularly

### Deployment Options

**Option 1: Gunicorn + Nginx**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Option 2: Docker**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

**Option 3: PythonAnywhere / Heroku / AWS**
- Follow platform-specific deployment guides
- Ensure environment variables are configured
- Use managed database services
- Enable automatic backups

## 📝 Logging & Audit

All actions are logged to `logs/phishaware.log`:
- Admin logins/logouts
- Campaign creation/sending
- Email delivery attempts
- Click events
- Quiz submissions
- Report accesses

For compliance, ensure logs are:
- Stored securely
- Retained according to policy
- Not accessible to employees
- Regularly reviewed

## 🔄 Integration & APIs

### Internal APIs
- `GET /api/campaigns/<id>/employees` - Employee enrollment status
- `POST /api/quiz/submit` - Submit quiz answers
- `GET /api/campaigns/<id>/campaign-stats` - Campaign statistics

### Webhook Support (Future)
- Integration with Slack/Teams for notifications
- HR system integration for bulk employee upload
- LDAP/AD integration for employee directory

## 📚 Best Practices

1. **Campaign Timing:** Vary days/times to prevent prediction
2. **Target Selection:** Rotate departments to ensure coverage
3. **Feedback Loop:** Discuss results in team meetings
4. **Content Updates:** Refresh email content quarterly
5. **Gradual Difficulty:** Start soft, increase complexity
6. **Positive Reinforcement:** Reward improved awareness
7. **Executive Support:** Get leadership endorsement
8. **Legal Review:** Have legal review campaigns
9. **Privacy Notice:** Include in employee handbook
10. **Training Before:** Conduct awareness sessions first

## 🤝 Support & Contributing

For issues, questions, or contributions:
1. Check logs first: `logs/phishaware.log`
2. Review troubleshooting section
3. Contact your IT security team
4. Document detailed error messages

## ⚖️ Legal Compliance

This platform is provided for authorized security training. Ensure:
- Compliance with local labor laws
- Employee consent and notification
- Data protection regulations (GDPR, CCPA, etc.)
- Company security policies
- Industry-specific requirements

## 📄 License

This platform is provided as-is for organizational use. Modify and deploy as needed within your organization.

---

**PhishAware - Training Employees to Recognize and Avoid Phishing**

For additional documentation, see:
- Flask Documentation: https://flask.palletsprojects.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Bootstrap Documentation: https://getbootstrap.com/docs/

**Last Updated:** February 2026
