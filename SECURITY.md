# PhishAware Security Guidelines

## 🔒 Platform Security Features

### Authentication & Access Control
- **Admin Authentication:** Session-based login with PBKDF2 password hashing
- **Password Security:** 
  - Minimum recommended length: 12 characters
  - Uses Werkzeug's `generate_password_hash` with SHA256
  - No passwords stored in plain text
- **Session Management:**
  - Secure session cookies (HTTPOnly, SameSite=Strict)
  - Auto-logout after 1 hour of inactivity
  - Session tokens are cryptographically secure

### Email Security
- **No Credential Capture:** Platform does not capture or store employee passwords
- **Fake Domains:** Must use fictional sender domains (never real company domain)
- **Clear Disclaimers:** Training notice included in all emails
- **Link Tracking:** Uses UUID tokens, not plaintext identifiers
- **No Attachments:** Avoids actual malware or dangerous content

### Data Protection
- **Database Security:**
  - Use SQLite for development (not production)
  - Use PostgreSQL with encryption for production
  - Enable database backups and replication
  - Restrict database access to application server only
- **Encryption:**
  - Enable HTTPS/TLS for all traffic (production)
  - Use certificate from trusted CA
  - Enable HSTS headers
- **Data Minimization:**
  - Only collect necessary data (email, click event, device info)
  - No personally identifiable information beyond email
  - No IP address logging for tracking purposes in some deployments

### Tracking Security
- **Click Tracking Tokens:** Generated using UUID v4 (cryptographically secure)
- **Token Uniqueness:** Each employee gets unique token per campaign
- **Token Expiration:** Can be configured via `CLICK_TRACKING_TIMEOUT`
- **Device Information:** Non-PII data only (browser type, device type)
- **No Fingerprinting:** Does not use browser fingerprinting or tracking pixels

### Audit Logging
- **Comprehensive Audit Trail:**
  - All admin actions logged
  - Campaign creation/modification tracked
  - Email sending logged
  - Click events recorded with timestamp
  - Quiz submission logged
- **Log Storage:** Secure storage in `logs/` directory
- **Log Access:** Restricted to administrators
- **Log Retention:** Implement per organizational policy

## 🛡️ Implementation Security

### Flask Configuration
```python
# Production settings (in config.py)
SESSION_COOKIE_SECURE = True      # HTTPS only
SESSION_COOKIE_HTTPONLY = True    # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Strict'
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
```

### Database Models
- **Foreign Keys:** All relationships enforced at DB level
- **Cascade Deletes:** Prevent orphaned records
- **Constraints:** Unique constraints on critical fields
- **Indexes:** Optimized for query performance and security

### Input Validation
- **Email Validation:** Regex pattern matching
- **HTML Escaping:** Jinja2 auto-escaping enabled
- **SQL Injection:** SQLAlchemy parameterized queries
- **CSRF Protection:** Recommended (Flask-WTF) - implement in production

### Error Handling
- **No Stack Traces:** Production errors don't expose internals
- **Logging:** All errors logged for troubleshooting
- **User-Friendly:** Non-technical error messages to users

## 🔐 Deployment Security

### Pre-Deployment Checklist

```
□ Change default admin password
□ Generate strong SECRET_KEY
□ Set FLASK_ENV=production
□ Enable HTTPS/TLS
□ Use PostgreSQL (not SQLite)
□ Configure email provider securely
□ Enable database backups
□ Set SESSION_COOKIE_SECURE=True
□ Configure firewall rules
□ Enable rate limiting
□ Set up monitoring/alerting
□ Review all user accounts
□ Test email configuration
□ Backup encryption keys
□ Enable audit logging
□ Configure log rotation
```

### Production Environment (.env)
```env
FLASK_ENV=production
DEBUG=False
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
SESSION_COOKIE_SECURE=True
SQLALCHEMY_DATABASE_URI=postgresql://user:pass@localhost/phishaware
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=<your-api-key>
SERVER_URL=https://phishaware.company.com
```

### Web Server Security (Nginx/Apache)
```nginx
# Example Nginx configuration
server {
    listen 443 ssl http2;
    server_name phishaware.company.com;
    
    ssl_certificate /etc/ssl/certs/company.crt;
    ssl_certificate_key /etc/ssl/private/company.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    proxy_pass http://localhost:5000;
}
```

### Firewall Rules
```
ALLOW: HTTPS (443) from company network
ALLOW: SSH (22) from admin network only
DENY: Direct database access from internet
DENY: SMTP from internet (use SendGrid/Mailtrap)
```

## ⚖️ Compliance & Legal

### GDPR Compliance
- **Consent:** Obtain explicit opt-in before campaigns
- **Data Minimization:** Collect only necessary data
- **Right to Access:** Provide reports showing personal data
- **Right to Deletion:** Implement data deletion mechanism
- **Privacy Notice:** Include in employee handbook

### CCPA Compliance (California)
- **Disclosure:** Inform about data collection
- **Opt-Out:** Allow employee opt-out
- **Data Access:** Provide access upon request
- **No Sale:** Do not sell employee data

### Industry Standards
- **ISO 27001:** Information security management
- **NIST Cybersecurity Framework:** Security practices
- **SOC 2:** Controls for data security
- **HIPAA:** If healthcare organization

### Documentation Required
- Security policy
- Data protection agreement
- Incident response plan
- Backup and recovery plan
- Audit trail procedures

## 🚨 Security Incident Response

### If Unauthorized Access Suspected
1. **Isolate:** Disconnect from network immediately
2. **Preserve:** Do not modify logs
3. **Notify:** Alert security/compliance team
4. **Forensics:** Engage incident response team
5. **Document:** Record timeline and actions
6. **Notify:** Inform affected employees if needed
7. **Review:** Conduct post-incident analysis

### If Email Credentials Compromised
1. Reset all admin passwords
2. Review audit logs for suspicious activity
3. Check email provider logs
4. Notify email provider of potential compromise
5. Enable multi-factor authentication (if supported)

### If Database Compromised
1. Restore from clean backup
2. Invalidate all sessions
3. Change database credentials
4. Review all data access
5. Conduct forensic analysis
6. Notify stakeholders

## 🔍 Security Testing

### Regular Security Audits
```bash
# Dependency security check
pip check

# Find known vulnerabilities
pip install safety
safety check

# Code analysis
pip install bandit
bandit -r .
```

### Penetration Testing
- Conduct at least annually
- Test authentication bypass
- Test database security
- Test input validation
- Test admin functions
- Test report generation

### Security Scanning
- Web application firewall (WAF)
- Intrusion detection system (IDS)
- Log analysis and SIEM
- Vulnerability scanning

## 🔑 Key Management

### SECRET_KEY
```python
# Generate secure key
import secrets
key = secrets.token_urlsafe(32)
print(f"SECRET_KEY={key}")
```

### Database Credentials
- Use environment variables only
- Never commit to Git
- Rotate credentials quarterly
- Use strong passwords (20+ characters)

### Email Provider Credentials
- Use API keys where available
- Rotate keys periodically
- Use separate keys for dev/prod
- Monitor for unauthorized usage

### SSL/TLS Certificates
- Use trusted CA (not self-signed)
- Auto-renew before expiration
- Monitor expiration dates
- Use high-strength ciphers

## 👥 User Management

### Default Credentials
Change immediately in production:
- Username: `admin`
- Password: `admin123`

### Create Secure Passwords
```
✓ Minimum 12 characters
✓ Mix of uppercase and lowercase
✓ Include numbers and symbols
✓ Unique for each account
✓ Change every 90 days
✗ Not based on personal info
✗ Not reused across systems
```

### Multi-Factor Authentication
Implement where possible:
- TOTP (Time-based One-Time Password)
- SMS/Email verification
- Hardware tokens

## 📊 Security Monitoring

### Metrics to Monitor
- Failed login attempts
- Admin action frequency
- Email sending anomalies
- Click rate spikes
- Database query performance
- Error rates
- Response times

### Alerts to Set
- Multiple failed logins
- Unusual admin activity
- Database connection failures
- Email sending failures
- Disk space warnings
- Memory usage spikes

### Log Monitoring
```bash
# Monitor for errors
tail -f logs/phishaware.log | grep ERROR

# Monitor for security events
grep "LOGIN\|SEND_EMAIL\|DELETE" logs/phishaware.log

# Check for unauthorized access
grep "403\|404\|500" logs/phishaware.log
```

## 🔄 Updates & Patching

### Keep Dependencies Updated
```bash
# Check for updates
pip list --outdated

# Update Flask
pip install --upgrade Flask

# Test after updates
pytest tests/
```

### Monitor Security Advisories
- Subscribe to Flask security mailing list
- Monitor SQLAlchemy updates
- Follow Python security notices
- Check GitHub security alerts

### Backup Strategy
- Daily automated backups
- Test backup restoration monthly
- Store backups offsite
- Encrypt backup data
- Document recovery procedures

## 📚 Security Resources

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Flask Security: https://flask.palletsprojects.com/
- SQLAlchemy Security: https://docs.sqlalchemy.org/
- Python Security: https://python.readthedocs.io/

## ✅ Security Checklist Summary

- [ ] Change default admin password
- [ ] Generate strong SECRET_KEY
- [ ] Configure HTTPS/TLS
- [ ] Enable HSTS headers
- [ ] Use PostgreSQL in production
- [ ] Encrypt database connections
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Set up automated backups
- [ ] Enable rate limiting
- [ ] Implement monitoring/alerting
- [ ] Document security procedures
- [ ] Conduct security training
- [ ] Perform regular security audits
- [ ] Test incident response plan

---

**Last Updated:** February 2026

For questions or security reports, contact your IT security team or compliance department.
