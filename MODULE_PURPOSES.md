# PhishAware - Module Purpose Guide

## Python Project Structure Explanation

### Core Application Files

#### `app.py` (450+ lines)
**Purpose:** Main Flask application entry point and route handlers

**Key Responsibilities:**
- Flask app initialization and configuration
- Route handlers for all endpoints (admin, awareness, quiz, tracking)
- Session management and authentication decorators
- Database initialization and ORM setup
- Error handling and HTTP response management
- API endpoints for AJAX calls
- Audit logging wrapper functions

**Key Functions:**
- `login()` / `logout()` - Admin authentication
- `admin_dashboard()` - Overview page
- `create_campaign()` - Campaign creation
- `send_campaign_emails()` - Email distribution
- `track_click_event()` - Click tracking redirect
- `awareness_portal()` - Training content display
- `quiz_page()` - Quiz interface
- `submit_quiz()` - Quiz submission and grading
- All report routes

---

#### `config.py` (80+ lines)
**Purpose:** Centralized configuration management

**Key Responsibilities:**
- Environmental variable loading
- Configuration class definitions
- Email provider settings
- Database connection URI
- Security settings (session cookies, lifetime)
- Application constants (quiz time limit, awareness thresholds)

**Configuration Classes:**
- `Config` - Base configuration for all environments
- `DevelopmentConfig` - Development-specific settings
- `ProductionConfig` - Production-ready settings
- `TestingConfig` - Testing environment settings

**Key Variables:**
- Secret key for session security
- Database URL
- Email provider credentials
- SMTP/SendGrid settings
- Cookie security flags
- Logging configuration

---

### Database Module

#### `database/models.py` (300+ lines)
**Purpose:** SQLAlchemy ORM models defining database schema

**Database Tables & Models:**

1. **Admin**
   - Admin user accounts
   - Password hashes (PBKDF2)
   - Login tracking

2. **Campaign**
   - Phishing simulation campaigns
   - Email content and sender info
   - Phishing attack type
   - Campaign status tracking

3. **Employee**
   - Employee participants
   - Email addresses
   - Department information

4. **CampaignEmployee** (Junction Table)
   - Links campaigns and employees
   - Tracks individual enrollment status
   - Unique tracking tokens per enrollment
   - Click status
   - Awareness level per campaign

5. **ClickTracking**
   - Records individual click events
   - Device/browser information
   - Click timing
   - User agent data

6. **QuizResult**
   - Quiz submission records
   - Scores and pass/fail
   - Question answers (JSON)
   - Time taken
   - Completion timestamp

7. **RiskScore**
   - Calculated awareness score
   - Risk assessment results
   - Email behavior analysis
   - Overall awareness level

8. **AuditLog**
   - Security audit trail
   - Admin action logging
   - Campaign send tracking
   - Compliance documentation

---

### Email Service Module

#### `email_service/mailer.py` (250+ lines)
**Purpose:** Email sending and template generation

**Key Classes:**
- `EmailService` - Abstract base class
- `MailtrapEmailService` - Sends via Mailtrap SMTP
- `SendGridEmailService` - Sends via SendGrid API

**Key Functions:**
- `send_email()` - Send email to recipient
- `get_email_service()` - Factory function to get configured provider
- `generate_tracking_link()` - Create unique employee link
- `generate_html_email()` - Create email template with tracking
- `send_phishing_simulation_email()` - Main campaign email send

**Features:**
- SMTP authentication support
- SendGrid API integration
- HTML/plain text email composition
- Pixel tracking for open detection
- Tracking link injection
- Error handling and logging

---

### Tracking Module

#### `tracking/click_tracker.py` (300+ lines)
**Purpose:** Click event tracking and user agent analysis

**Key Functions:**
- `generate_tracking_token()` - UUID-based unique identifier
- `parse_device_info()` - Browser/OS detection from User-Agent
- `get_device_type()` - Determine device (desktop/mobile/tablet)
- `track_click()` - Record click event to database
- `get_click_statistics()` - Aggregate click data for reports
- `get_employee_click_details()` - Individual employee history

**Data Captured:**
- Click timestamp
- IP address
- User agent string
- Device type
- Browser information
- Operating system
- Device/browser breakdown

**Features:**
- Prevents duplicate clicks (idempotent)
- Device type detection
- Browser identification
- Statistics aggregation
- Employee-level filtering
- Campaign-level filtering

---

### Quiz Module

#### `quiz/quiz_engine.py` (350+ lines)
**Purpose:** Quiz management, scoring, and educational content

**Pre-built Question Banks:**
- **Credential Harvesting:** 5 questions about password phishing
- **Malware Distribution:** 5 questions about attachment safety
- **Urgent Action:** 5 questions about CEO fraud/pressure tactics

**Questions Structure:**
```python
{
    'id': 'q1',
    'question': 'The actual question',
    'options': ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
    'correct_answer': 2,  # Index of correct answer
    'explanation': 'Why this is correct'
}
```

**Key Functions:**
- `get_quiz_questions()` - Get questions for phishing type
- `validate_quiz_answer()` - Check answers and calculate score
- `save_quiz_result()` - Persist results to database
- `get_quiz_statistics()` - Aggregate quiz metrics

**Scoring:**
- Each question worth equal points
- Automatic grading
- Score = (Correct / Total) × 100
- Pass threshold: 70%
- Tracks time taken

**Features:**
- Question-based learning
- Instant feedback
- Comprehensive explanations
- Pass/fail determination
- Analytics aggregation

---

### Detection Engine Module

#### `detection_engine/risk_scoring.py` (350+ lines)
**Purpose:** Risk assessment and awareness level calculation

**Key Class:**
- `RiskScoringEngine` - Calculates overall risk and awareness

**Scoring Algorithm:**
```
Overall Score = (Quiz Score × 0.4) + (Email Behavior × 0.6)

Email Behavior:
- Didn't click: 100 points
- Click <1 min: 30 points
- Click <5 min: 55 points
- Click <30 min: 80 points
- Click <1 hr: 85 points
- Click >1 hr: 90 points

Awareness Levels:
- High: ≥80
- Medium: 50-79
- Low: <50
```

**Key Functions:**
- `calculate_email_risk()` - Risk from email interaction
- `calculate_quiz_awareness_score()` - Score from quiz
- `calculate_overall_awareness()` - Combined assessment
- `calculate_risk_level()` - Overall risk determination
- `calculate_score()` - Complete assessment
- `calculate_and_save_risk_score()` - DB persistence
- `get_campaign_risk_summary()` - Campaign-wide metrics
- `get_department_risk_analysis()` - Department breakdown

**Metrics Generated:**
- Email behavior score
- Quiz performance score
- Overall awareness score
- Awareness level (High/Medium/Low)
- Risk level (Low/Medium/High)
- Department comparisons

---

### Template Files (Jinja2)

#### `templates/base.html`
**Purpose:** Base template with navigation and layout

**Features:**
- Navigation bar for admins
- Flash message display
- Bootstrap 5 integration
- Footer with compliance notice
- Block structure for child templates

#### `templates/login.html`
**Purpose:** Admin login interface

**Features:**
- Credentials form
- Default credential display
- Security notice
- Responsive design

#### `templates/admin/dashboard.html`
**Purpose:** Admin dashboard overview

**Displays:**
- Statistics cards (campaigns, employees, clicks)
- Quick action buttons
- Recent campaigns table

#### `templates/admin/campaign_form.html`
**Purpose:** Create/edit campaign form

**Fields:**
- Campaign name and description
- Phishing type selection
- Sender information
- Email subject and body (HTML)
- Tips sidebar

#### `templates/awareness/portal.html`
**Purpose:** Phishing awareness training portal

**Sections:**
- Training disclaimer
- Attack type explanation
- Red flags to spot
- Prevention tips
- Psychology manipulation techniques
- Next step (quiz link)

#### `templates/quiz/quiz.html`
**Purpose:** Interactive quiz interface

**Features:**
- Countdown timer
- Multiple choice questions
- Progress indicator
- Form validation
- AJAX submission

#### `templates/quiz/results.html`
**Purpose:** Quiz feedback and results

**Displays:**
- Score and performance
- Question-by-question review
- Correct/incorrect answers
- Explanations for each question
- Pass/fail status

#### Admin Report Templates
- `click_statistics.html` - Click analysis with charts
- `quiz_analytics.html` - Quiz metrics and statistics
- `awareness_report.html` - Employee awareness summary

---

### Static Files

#### `static/css/style.css` (250+ lines)
**Purpose:** Application styling and responsive design

**Features:**
- Bootstrap 5 customizations
- Card hover animations
- Color scheme consistency
- Form styling
- Table styling
- Print-friendly styles
- Mobile responsiveness

#### `static/js/main.js` (200+ lines)
**Purpose:** JavaScript utilities and client-side logic

**Functions:**
- `showToast()` - Display notifications
- `formatTime()` - Time formatting
- `getQueryParams()` - URL parameter parsing
- `exportTableToCSV()` - Download functionality
- `confirmAction()` - Confirmation dialogs
- `apiCall()` - API request wrapper
- `formatDate()` - Date formatting
- `isValidEmail()` - Email validation
- `parseEmailList()` - Batch email parsing

---

### Supporting Files

#### `requirements.txt`
**Purpose:** Python package dependencies

**Key Packages:**
- Flask - Web framework
- SQLAlchemy - ORM
- Flask-SQLAlchemy - Flask + SQLAlchemy integration
- Werkzeug - Security utilities
- Mailtrap - Email testing
- sendgrid - Email production
- Gunicorn - Production server
- python-dotenv - Environment variables

#### `setup.py`
**Purpose:** Interactive setup wizard

**Functions:**
- Initialize database schema
- Create admin user
- Generate sample data
- Configuration wizard

#### `.env.example`
**Purpose:** Environment variable template

**Variables:**
- Flask configuration
- Database connection
- Email credentials
- Application settings

#### `README.md`, `QUICKSTART.md`, `SECURITY.md`
**Purpose:** Comprehensive documentation

**Contents:**
- Setup instructions
- Usage guides
- Security guidelines
- Best practices
- Troubleshooting
- Deployment guide

---

## 🔄 Data Flow Summary

### Campaign Lifecycle
1. Admin creates campaign (app.py)
2. Admin adds employees (app.py)
3. Admin sends emails (mailer.py)
4. Email records created (models.py)
5. Employee receives email
6. Employee clicks link
7. Click tracked (click_tracker.py)
8. Employee redirected (app.py)
9. Employee completes quiz (quiz_engine.py)
10. Score calculated (risk_scoring.py)
11. Admin views reports (app.py)

### Employee Journey
1. Receive phishing email
2. Click tracking link → track_click()
3. Redirect to awareness portal → awareness_portal()
4. Read training content
5. Navigate to quiz → quiz_page()
6. Answer questions → submit_quiz()
7. View results → quiz_results()
8. Risk score calculated → calculate_and_save_risk_score()

### Admin Workflow
1. Login → session management
2. Create campaign → Campaign model
3. Add employees → CampaignEmployee model
4. Send emails → mailer.py, ClickTracking
5. Monitor clicks → click_tracker.py
6. View reports → get_campaign_risk_summary()
7. Analyze by department → get_department_risk_analysis()

---

## 🎯 Module Dependencies

```
app.py
├── config.py (configuration)
├── database/models.py (data access)
├── email_service/mailer.py (email sending)
├── tracking/click_tracker.py (click events)
├── quiz/quiz_engine.py (quizzes)
└── detection_engine/risk_scoring.py (analysis)

Models
├── Admin, Campaign, Employee
├── CampaignEmployee (junction)
├── ClickTracking, QuizResult
├── RiskScore
└── AuditLog

Templates
├── base.html (layout)
├── admin/* (admin pages)
├── awareness/* (training content)
└── quiz/* (quiz pages)

Static
├── css/style.css (styling)
└── js/main.js (client logic)
```

---

This modular architecture allows easy maintenance, testing, and future enhancements while keeping code organized and purpose-driven.
