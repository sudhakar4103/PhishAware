# Email Configuration Guide

This guide explains how to set up email sending for PhishAware.

## Three Email Sending Options

### 1. **Demo Mode (Default - No Setup Required)**
By default, PhishAware runs in **demo mode** where emails are logged but not actually sent. This is perfect for testing the UI and workflows.

```
EMAIL_PROVIDER=mailtrap
MAILTRAP_USERNAME=
MAILTRAP_PASSWORD=
```

When credentials are empty, emails log as "sent (demo mode)". This allows you to test the complete flow without email infrastructure.

---

### 2. **Mailtrap (Recommended for Testing)**

Mailtrap provides a safe inbox for testing. Emails go to your Mailtrap inbox instead of real employees.

#### Setup:
1. Sign up at [mailtrap.io](https://mailtrap.io)
2. Create an inbox
3. Get credentials from **Integrations** → **SMTP**
4. Add to `.env`:
   ```
   EMAIL_PROVIDER=mailtrap
   MAILTRAP_USERNAME=your_mailtrap_username
   MAILTRAP_PASSWORD=your_mailtrap_password
   MAILTRAP_HOST=live.mailtrap.io
   MAILTRAP_PORT=465
   ```

#### Test:
1. Create a campaign and add test employees
2. Click **Test Email** button to send a test
3. Check your Mailtrap inbox

---

### 3. **SendGrid (Production Email)**

SendGrid sends real emails to recipients' actual email addresses.

#### Setup:
1. Sign up at [sendgrid.com](https://sendgrid.com)
2. Create an API Key in **Settings** → **API Keys**
3. Add to `.env`:
   ```
   EMAIL_PROVIDER=sendgrid
   SENDGRID_API_KEY=your_sendgrid_api_key
   ```

#### Test:
1. Create a campaign and add test employees
2. Click **Test Email** button
3. Check the admin's email for the test

#### Important - Sender Email Verification:
Before sending, verify the sender email in SendGrid:
1. Go to **Settings** → **Sender Authentication**
2. Verify the domain or single sender email used in `SENDER_EMAIL`

---

## .env Configuration

Copy `.env.example` to `.env` and update:

```bash
cp .env.example .env
```

Edit `.env` with your email provider settings:

```dotenv
# Email Provider (mailtrap or sendgrid)
EMAIL_PROVIDER=mailtrap

# Mailtrap Configuration (for testing)
MAILTRAP_USERNAME=your_mailtrap_username
MAILTRAP_PASSWORD=your_mailtrap_password
MAILTRAP_HOST=live.mailtrap.io
MAILTRAP_PORT=465

# SendGrid Configuration (for production)
# SENDGRID_API_KEY=your_sendgrid_api_key

# Application Settings
SENDER_EMAIL=your-email@your-domain.com
SENDER_NAME=Security Training Team
SERVER_URL=http://localhost:5000
```

---

## Email Flow

1. **Admin creates campaign** → Selects phishing template
2. **Admin adds employees** → Paste email list
3. **Admin tests email** → Click "Test Email" to verify configuration
4. **Admin sends emails** → Click "Send Emails" to launch campaign
5. **Employees receive** → Email with realistic phishing scenario
6. **Click tracking** → Link redirects to awareness training
7. **Quiz** → Employee completes awareness quiz
8. **Results** → Admin sees click rates and quiz scores

---

## Troubleshooting

### Emails showing "failed (demo mode)"
- Configure real email credentials in `.env`
- Restart the app: `python app.py`

### Test email not arriving
- Check spam/junk folder
- Verify sender email is verified in SendGrid
- Check app logs for errors: `tail logs/phishaware.log`

### SMTP Authentication Failed
- Double-check credentials from email provider
- Ensure `MAILTRAP_PORT=465` (not 587)
- Mailtrap uses username, not email address

### SendGrid: Invalid from address
- Verify sender email domain in SendGrid settings
- Use a verified sender or verified domain

---

## Demo to Production Checklist

Before going to production:

- [ ] Set up real email provider (SendGrid/Mailtrap)
- [ ] Verify sender email domain
- [ ] Test email sending with small group
- [ ] Set `SERVER_URL` to actual domain (e.g., https://phishaware.company.com)
- [ ] Enable `SESSION_COOKIE_SECURE=True` and use HTTPS
- [ ] Update `SECRET_KEY` to a secure value
- [ ] Set `FLASK_ENV=production`

---

## Email Templates

PhishAware includes 5 pre-built phishing templates covering:
- Account verification (credential harvesting)
- Secure document (credential harvesting)
- Invoice payment (malware simulation)
- Password expiration (urgent action)
- Policy acknowledgement (urgent action)

Emails automatically include:
- Tracking link for click detection
- Training disclaimer
- Support for both HTML and plain text

No HTML editing required—admins just select a template and send!
