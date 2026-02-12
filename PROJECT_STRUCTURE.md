# PhishAware - Restructured Application

## 🎯 Professional Project Structure

The application has been restructured to follow Flask best practices with:
- **App Factory Pattern**
- **Blueprint-based Architecture**
- **Service Layer Separation**
- **Modular Design**

## 📁 Project Structure

```
PhishAware/
├── app/                          # Application package
│   ├── __init__.py              # App factory
│   ├── routes/                  # Blueprints
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication (login/logout)
│   │   ├── admin.py            # Admin dashboard & reports
│   │   ├── campaigns.py        # Campaign management
│   │   ├── tracking.py         # Click tracking
│   │   ├── awareness.py        # Awareness portal & quiz
│   │   └── api.py              # JSON API endpoints
│   ├── services/                # Business logic layer
│   ├── utils/                   # Utilities
│   │   ├── decorators.py       # Custom decorators
│   │   └── helpers.py          # Helper functions
│   └── models/                  # Future: Split database models
│
├── database/                     # Database models
│   ├── models.py               # SQLAlchemy models
│   └── __init__.py
│
├── email_service/               # Email sending
│   ├── mailer.py
│   └── __init__.py
│
├── detection_engine/            # Risk scoring
│   ├── detection_engine.py
│   ├── risk_scoring.py
│   └── __init__.py
│
├── tracking/                    # Click tracking
│   ├── click_tracker.py
│   └── __init__.py
│
├── quiz/                        # Quiz engine
│   ├── quiz_engine.py
│   └── __init__.py
│
├── static/                      # Static files (CSS, JS, images)
│   ├── css/
│   └── js/
│
├── templates/                   # Jinja2 templates
│   ├── base.html
│   ├── login.html
│   ├── admin/
│   ├── awareness/
│   └── quiz/
│
├── instance/                    # Instance-specific files
│   └── phishaware.db           # SQLite database
│
├── logs/                        # Application logs
│
├── data/                        # Data files
│   └── phishing_templates.json
│
├── run.py                       # Application entry point ⭐ NEW
├── app.py                       # Old entry point (deprecated)
├── setup.py                     # Database setup script
├── config.py                    # Configuration management
├── requirements.txt             # Python dependencies
└── README.md                    # Documentation

```

## 🚀 Quick Start

### 1. Start the Application

**NEW WAY (Recommended):**
```bash
python run.py
```

**OLD WAY (Still works):**
```bash
python app.py
```

### 2. Access Application
- **URL:** http://localhost:5000
- **Login:** admin / admin123

## 🔧 Key Improvements

### 1. **App Factory Pattern** (`app/__init__.py`)
- Creates Flask app with `create_app()` function
- Easier testing and configuration management
- Support for multiple environments

### 2. **Blueprints** (`app/routes/`)
- **auth**: Login/logout functionality
- **admin**: Dashboard and reports
- **campaigns**: Campaign CRUD operations
- **tracking**: Click tracking
- **awareness**: Portal and quiz
- **api**: JSON endpoints

### 3. **Service Layer** (`app/services/`)
- Business logic separated from routes
- Reusable functions
- Easier testing

### 4. **Utilities** (`app/utils/`)
- `decorators.py`: @login_required decorator
- `helpers.py`: Audit logging, IP detection

## 📋 URL Structure

### Authentication
- `GET/POST /login` - Admin login
- `POST /logout` - Logout

### Admin Dashboard
- `GET /admin/dashboard` - Overview
- `GET /admin/reports/click-statistics` - Click stats
- `GET /admin/reports/quiz-analytics` - Quiz analytics
- `GET /admin/reports/awareness-report` - Awareness levels

### Campaigns
- `GET /admin/campaigns/` - List campaigns
- `GET/POST /admin/campaigns/create` - Create campaign
- `GET /admin/campaigns/<id>` - Campaign details
- `POST /admin/campaigns/<id>/add-employees` - Add employees
- `POST /admin/campaigns/<id>/send-emails` - Send emails
- `POST /admin/campaigns/<id>/test-email` - Test email

### Tracking & Awareness
- `GET /track/click/<campaign>/<token>` - Track click
- `GET /awareness/<campaign>/<token>` - Awareness portal
- `GET /quiz/<campaign>/<token>` - Quiz page
- `GET /quiz/results/<token>` - Quiz results

### API
- `GET /api/campaigns/<id>/employees` - Get employees
- `POST /api/quiz/submit` - Submit quiz

## 🔒 Security Features

- Session-based authentication
- Login required decorator
- Audit logging
- IP address tracking
- CSRF protection (Flask default)

## 🧪 Testing

The new structure makes testing easier:

```python
# test_auth.py
from app import create_app, db

def test_login():
    app = create_app('testing')
    with app.test_client() as client:
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        assert response.status_code == 302  # Redirect
```

## 📦 Development

### Running in Development
```bash
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development     # Windows CMD
$env:FLASK_ENV="development"  # Windows PowerShell

python run.py
```

### Running in Production
```bash
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

## 🔄 Migration from Old Structure

Both `app.py` and `run.py` work currently. Benefits of `run.py`:
- ✅ Cleaner separation of concerns
- ✅ Better for testing
- ✅ Supports multiple configurations
- ✅ Standard Flask project structure
- ✅ Easier to scale

## 📚 Next Steps

1. ✅ App factory pattern implemented
2. ✅ Blueprints created
3. ✅ Utilities separated
4. 🔄 Create service layer
5. 🔄 Add unit tests
6. 🔄 Add database migrations (Flask-Migrate)
7. 🔄 Split models into separate files
8. 🔄 Add API documentation (Swagger)

## 💡 Tips

- Use `run.py` as the entry point going forward
- Add new routes to appropriate blueprints
- Keep business logic in `app/services/`
- Add utilities to `app/utils/`
- Test individual components with blueprints

## 🐛 Troubleshooting

**Import errors?**
```bash
# Make sure you're in the project root
cd PhishAware
python run.py
```

**Database issues?**
```bash
# Reset database
python setup.py
```

**Module not found?**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

---

**🎉 The application is now structured as a professional Flask project!**
