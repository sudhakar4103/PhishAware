# PhishAware - Phishing Awareness Training Platform

## Overview

Phishing simulation training platform for authorized employee security awareness testing. Admins send controlled phishing emails, track clicks, and generate awareness reports. **⚠️ Requires explicit employee consent.**

## Features

- Admin dashboard for campaign management
- Phishing email sending with real-time tracking
- Employee awareness portal & quiz
- Click statistics & risk scoring
- Audit logging & compliance reports
- No credential/password capture

## Tech Stack

- **Backend:** Python 3.8+, Flask
- **Database:** SQLite / PostgreSQL
- **ORM:** SQLAlchemy
- **Email:** Mailtrap (test) / SendGrid (production)
- **Frontend:** HTML5, Bootstrap 5

## Quick Start

1. **Setup environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure `.env` file:**
   ```
   FLASK_ENV=development
   SECRET_KEY=your-secret-key
   EMAIL_PROVIDER=mailtrap
   MAILTRAP_USERNAME=your-username
   MAILTRAP_PASSWORD=your-password
   ```

3. **Initialize database:**
   ```bash
   python -c "from app import app, init_db; init_db()"
   ```

4. **Run application:**
   ```bash
   python app.py
   ```

5. **Access at:** http://localhost:5000
   - **Default login:** admin / admin123 (change in production!)

## Usage

1. **Login** with admin credentials
2. **Dashboard** → Click "New Campaign"
3. **Configure:** Campaign name, phishing type, subject, email body
4. **Add Employees:** Upload email list
5. **Send:** Click "Send Emails"
6. **Monitor:** Track clicks, quiz completion, risk scores
7. **Reports:** View click stats, quiz analytics, awareness levels

## Project Structure

```
PhishAware/
├── app.py                 # Main Flask app
├── config.py              # Configuration
├── requirements.txt       # Dependencies
├── database/models.py     # Database models
├── email_service/mailer.py    # Email sending
├── tracking/click_tracker.py  # Click tracking
├── quiz/quiz_engine.py    # Quiz logic
├── detection_engine/risk_scoring.py  # Risk calculation
├── templates/             # HTML templates
├── static/                # CSS & JS
└── logs/                  # Application logs
```

## Security

- Session-based admin authentication
- No credential/password capture
- Unique tracking tokens per employee
- Audit logging of all actions
- GDPR-compliant data handling

## Risk Scoring

**Score = (Quiz Score × 0.4) + (Email Behavior Score × 0.6)**

- **Did not click:** 100 points
- **Clicked within 1 min:** 30 points
- **Clicked 1-5 min:** 55 points
- **Clicked 5-30 min:** 80 points
- **Clicked after 30 min:** 90 points

**Awareness Levels:** High (≥80), Medium (50-79), Low (<50)

## Email Configuration

**Mailtrap (Testing):**
```
EMAIL_PROVIDER=mailtrap
MAILTRAP_USERNAME=your_username
MAILTRAP_PASSWORD=your_password
```

**SendGrid (Production):**
```
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your_api_key
```

## Important - Ethical & Legal Guidelines

✅ **DO:**
- Get explicit employee consent BEFORE campaigns
- Use clear training disclaimers
- Document compliance with policy

❌ **DO NOT:**
- Send without consent
- Use real company domains
- Capture actual passwords

## Troubleshooting

**Emails not sending:** Check Mailtrap/SendGrid credentials in `.env`

**Database errors:** 
```bash
rm phishaware.db
python -c "from app import init_db; init_db()"
```

**Port in use:**
```bash
python -c "from app import app; app.run(port=5001)"
```

---

**PhishAware** - Phishing Awareness Training Platform

For more docs, see: [Flask](https://flask.palletsprojects.com/) | [SQLAlchemy](https://docs.sqlalchemy.org/) | [Bootstrap](https://getbootstrap.com/)
