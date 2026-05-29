# PhishAware - Quick Start Guide

## 5-Minute Setup

### 1. Clone/Extract Project
```bash
cd PhishAware
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Copy Environment File
```bash
cp .env.example .env
# Edit .env with your Gmail SMTP credentials
```

### 5. Run Setup Script
```bash
python setup.py
# Follow prompts to create admin user
# Optionally create sample campaign
```

### 6. Start Application
```bash
python app.py
```

### 7. Access Platform
- **URL:** http://localhost:5000
- **Admin Login:** Use credentials created in step 5

---

## First Campaign

### Create Campaign
1. Login to admin dashboard
2. Click **"New Campaign"**
3. Fill in details:
   - Name: "Q1 Phishing Test"
   - Type: "Credential Harvesting"
   - Sender: "security@demo-company.com" (use FAKE domain)
   - Subject: "Action Required: Verify Your Account"
   - Template: Use provided HTML with red flags

### Add Employees
1. Click **"Add Employees"** on campaign
2. Paste test email addresses (one per line)
3. Click "Add Employees"

### Send Emails
1. Click **"Send Emails"** button
2. Confirm action
3. Watch emails arrive in inbox

### Track Results
1. Click links in received emails
2. Complete training quiz
3. View results in **Admin Dashboard**

---

## Key Features Quick Access

| Feature | URL | Purpose |
|---------|-----|---------|
| **Dashboard** | http://localhost:5000 | Overview & stats |
| **Campaigns** | /admin/campaigns | Manage campaigns |
| **Reports** | /admin/reports/awareness | View analytics |
| **Click Stats** | /admin/reports/click-statistics | Click analysis |
| **Quiz Analysis** | /admin/reports/quiz-analytics | Quiz metrics |

---

## Email Configuration

### Gmail SMTP
```env
GMAIL_USERNAME=your_username@gmail.com
GMAIL_APP_PASSWORD=your_app_password
GMAIL_SMTP_HOST=smtp.gmail.com
GMAIL_SMTP_PORT=587
```

---

## Testing Checklist

- [ ] Admin login works
- [ ] Can create campaign
- [ ] Can add employees
- [ ] Email sends to inbox
- [ ] Click link opens awareness portal
- [ ] Complete training quiz
- [ ] View results in admin dashboard
- [ ] View reports/analytics

---

## Troubleshooting

**Emails not sending?**
- Check .env file has correct credentials
- Verify email provider account is configured
- Check logs: `tail -f logs/phishaware.log`

**Database errors?**
```bash
rm phishaware.db
python setup.py
```

**Port already in use?**
```bash
python -c "from app import app; app.run(port=5001)"
```

**Can't login?**
- Check admin credentials (created in setup.py)
- Ensure database was initialized
- Check logs for errors

---

## Next Steps

1. **Read** README.md for full documentation
2. **Review** SECURITY.md for security practices
3. **Configure** .env with your email provider
4. **Create** admin users for your team
5. **Plan** first campaign targeting
6. **Get** employee consent before launching
7. **Execute** pilot campaign
8. **Analyze** results
9. **Iterate** based on feedback

---

## Important Reminders

⚠️ **Authorization:** Get explicit consent from employees before any campaign

⚠️ **Ethics:** Focus on training, not punishment

⚠️ **Privacy:** Collect minimal personal data

⚠️ **Security:** Change default password immediately

🔒 **Production:** Enable HTTPS and use strong database

---

For detailed documentation, see: **README.md**
For security guidelines, see: **SECURITY.md**
