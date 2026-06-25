## Gmail SMTP Setup

PhishAware uses Gmail SMTP only. Use a Google app password for the account that sends campaign mail.

#### Setup:
1. Enable 2-Step Verification for the Gmail account.
2. Create an app password in Google Account security settings.
3. Add to `.env`:
   ```
   GMAIL_USERNAME=yourgmail@gmail.com
   GMAIL_APP_PASSWORD=your_16_char_app_password
   GMAIL_SMTP_HOST=smtp.gmail.com
   GMAIL_SMTP_PORT=587
   SENDER_EMAIL=yourgmail@gmail.com
   ```

#### Test:
1. Create a campaign and add test employees
2. Click **Test Email** button to send a test
3. Check the Gmail inbox and sent items
#### Important - Sender Email Verification:
Before sending, verify the Gmail sender account is the one you want to use for campaign mail.

---

## .env Configuration

Copy `.env.example` to `.env` and update:

```bash
cp .env.example .env
```

Edit `.env` with your Gmail SMTP settings:

```dotenv
# Gmail SMTP Configuration
GMAIL_USERNAME=yourgmail@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
GMAIL_SMTP_HOST=smtp.gmail.com
GMAIL_SMTP_PORT=587

# Application Settings
SENDER_EMAIL=yourgmail@gmail.com
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

### Test email not arriving
- Check spam/junk folder
- Verify the Gmail app password is valid
- Check app logs for errors: `tail logs/phishaware.log`

### SMTP Authentication Failed
- Double-check the Gmail username and app password
- Ensure `GMAIL_SMTP_PORT=587`
- Verify 2-Step Verification is enabled on the Gmail account

---

## Demo to Production Checklist

Before going to production:

- [ ] Set up Gmail app password
- [ ] Verify sender email address
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
