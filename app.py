
"""PhishAware - Phishing Awareness Training Platform
Version: 1.0.0
Date: February 12, 2026
"""
__version__ = '1.0.0'

import os
import logging
import re
from datetime import datetime
import uuid
import json

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_wtf.csrf import CSRFError

from config import get_config
from database.models import db, Admin, Campaign, Employee, CampaignEmployee, QuizResult, RiskScore, AuditLog
from email_service.mailer import get_email_service, send_phishing_simulation_email, generate_tracking_link
from tracking.click_tracker import track_click, get_click_statistics, get_employee_click_details
from quiz.quiz_engine import get_quiz_questions, save_quiz_result, get_quiz_statistics
from detection_engine.risk_scoring import calculate_and_save_risk_score, get_campaign_risk_summary, get_department_risk_analysis
from phishing_templates import get_phishing_templates, get_phishing_template_by_id


# Initialize Flask app
app = Flask(__name__)
app.config.from_object(get_config())
if not app.config.get('DEBUG', False):
    try:
        get_config().validate()
    except AttributeError:
        pass  # Only ProductionConfig has validate()

# Initialize rate limiter
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["200/day", "50/hour"])

# Initialize database
db.init_app(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(app.config['LOG_FILE']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# DECORATORS AND UTILITIES
# ============================================================================

def login_required(f):
    """Decorator to require admin login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            wants_json = (
                request.path.startswith('/api/')
                or request.is_json
                or 'application/json' in (request.headers.get('Accept', '') or '').lower()
                or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            )
            if wants_json:
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            flash('Please log in first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_client_ip():
    """Get client IP address. Trusts X-Forwarded-For only if app is behind a proxy."""
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for and app.config.get('TRUST_PROXY', False):
        # Only trust this header if explicitly configured to do so
        ip = forwarded_for.split(',')[0].strip()
        # Basic sanity check - reject obviously forged values
        if ip and ip != '127.0.0.1' and len(ip) < 46:
            return ip
    return request.remote_addr


def log_audit(action, resource_type, resource_id, details=None, admin_id=None):
    """Log audit event."""
    try:
        audit = AuditLog(
            log_id=str(uuid.uuid4()),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            admin_id=admin_id or session.get('admin_id'),
            details=details,
            ip_address=get_client_ip()
        )
        db.session.add(audit)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error logging audit: {str(e)}")


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/', methods=['GET'])
def index():
    """Home page redirects to login or dashboard."""
    if 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))


@limiter.limit("10/minute")
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.is_active and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            admin.last_login = datetime.utcnow()
            db.session.commit()
            
            log_audit('LOGIN_SUCCESS', 'admin', admin.id)
            logger.info(f'Admin {username} logged in successfully')
            
            return redirect(url_for('admin_dashboard'))
        
        log_audit('LOGIN_FAILED', 'admin', None, f'Failed login attempt: {username}')
        flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@limiter.limit("20/minute")
@app.route('/logout', methods=['POST'])
def logout():
    """Admin logout."""
    admin_id = session.get('admin_id')
    if admin_id:
        log_audit('LOGOUT', 'admin', admin_id)
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))


# ============================================================================
# ADMIN DASHBOARD ROUTES
# ============================================================================

@app.route('/admin/dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    """Admin dashboard overview."""
    admin = Admin.query.get(session['admin_id'])
    page = request.args.get('page', 1, type=int)
    campaigns_paginated = Campaign.query.filter_by(created_by_id=admin.id)\
        .order_by(Campaign.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    campaigns = campaigns_paginated.items
    
    total_campaigns = len(campaigns)
    total_employees = len(set(
        ce.employee_id for c in campaigns for ce in c.employees
    ))
    total_clicks = sum(ce.clicked for c in campaigns for ce in c.employees)
    
    return render_template(
        'admin/dashboard.html',
        admin=admin,
        total_campaigns=total_campaigns,
        total_employees=total_employees,
        total_clicks=total_clicks,
        campaigns=campaigns
    )


# ============================================================================
# CAMPAIGN MANAGEMENT ROUTES
# ============================================================================

@app.route('/admin/campaigns', methods=['GET'])
@login_required
def campaigns_list():
    """List all campaigns for admin."""
    admin = Admin.query.get(session['admin_id'])
    page = request.args.get('page', 1, type=int)
    campaigns = Campaign.query.filter_by(created_by_id=admin.id)\
        .order_by(Campaign.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/campaigns.html', campaigns=campaigns)


@app.route('/admin/campaigns/create', methods=['GET', 'POST'])
@login_required
def create_campaign():
    """Create new phishing simulation campaign."""
    templates = get_phishing_templates()

    if request.method == 'POST':
        try:
            template_id = request.form.get('template_id')
            selected_template = get_phishing_template_by_id(template_id)

            if not selected_template:
                flash('Please select a valid template', 'error')
                return render_template('admin/campaign_form.html', templates=templates)

            campaign = Campaign(
                campaign_id=str(uuid.uuid4()),
                name=request.form.get('name'),
                description=request.form.get('description'),
                sender_name=selected_template.get('sender_name'),
                sender_email=selected_template.get('sender_email'),
                subject_line=selected_template.get('subject_line'),
                phishing_type=selected_template.get('phishing_type'),
                email_template=selected_template.get('html'),
                created_by_id=session['admin_id'],
                status='draft'
            )
            
            db.session.add(campaign)
            db.session.commit()
            
            log_audit('CREATE_CAMPAIGN', 'campaign', campaign.campaign_id, 
                     f'Campaign: {campaign.name}')
            logger.info(f'Campaign created: {campaign.name}')
            
            flash('Campaign created successfully', 'success')
            return redirect(url_for('campaign_detail', campaign_id=campaign.campaign_id))
        
        except Exception as e:
            logger.error(f'Error creating campaign: {str(e)}')
            flash(f'Error creating campaign: {str(e)}', 'error')
    
    return render_template('admin/campaign_form.html', templates=templates)


@app.route('/admin/campaigns/<campaign_id>', methods=['GET'])
@login_required
def campaign_detail(campaign_id):
    """View campaign details and statistics."""
    campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
    
    if not campaign or campaign.created_by_id != session['admin_id']:
        flash('Campaign not found', 'error')
        return redirect(url_for('campaigns_list'))
    
    # Get statistics
    campaign_employees = CampaignEmployee.query.filter_by(campaign_id=campaign.id).all()
    sent_count = sum(1 for ce in campaign_employees if ce.email_sent_at)
    clicked_count = sum(1 for ce in campaign_employees if ce.clicked)
    completed_count = sum(1 for ce in campaign_employees if ce.status == 'completed')
    
    # Get risk summary
    risk_summary = get_campaign_risk_summary(campaign_id)
    
    return render_template(
        'admin/campaign_detail.html',
        campaign=campaign,
        total_employees=len(campaign_employees),
        sent_count=sent_count,
        clicked_count=clicked_count,
        completed_count=completed_count,
        click_rate=round((clicked_count / sent_count * 100) if sent_count > 0 else 0, 2),
        risk_summary=risk_summary
    )


@app.route('/admin/campaigns/<campaign_id>/add-employees', methods=['GET', 'POST'])
@login_required
def add_employees_to_campaign(campaign_id):
    """Add employees to campaign."""
    campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
    
    if not campaign or campaign.created_by_id != session['admin_id']:
        flash('Campaign not found', 'error')
        return redirect(url_for('campaigns_list'))
    
    if request.method == 'POST':
        try:
            email_list = request.form.get('email_list').split('\n')

            EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            invalid_emails = []
            added_count = 0

            for email in email_list:
                email = email.strip().lower()
                if not email:
                    continue
                if not EMAIL_RE.match(email):
                    invalid_emails.append(email)
                    continue
                
                # Create employee if doesn't exist
                employee = Employee.query.filter_by(email=email).first()
                if not employee:
                    employee = Employee(
                        employee_id=str(uuid.uuid4()),
                        email=email,
                        full_name=email.split('@')[0]
                    )
                    db.session.add(employee)
                    db.session.flush()
                
                # Check if already in campaign
                existing = CampaignEmployee.query.filter_by(
                    campaign_id=campaign.id,
                    employee_id=employee.id
                ).first()
                
                if not existing:
                    campaign_employee = CampaignEmployee(
                        campaign_id=campaign.id,
                        employee_id=employee.id,
                        tracking_token=str(uuid.uuid4()),
                        status='pending'
                    )
                    db.session.add(campaign_employee)
                    added_count += 1
            
            db.session.commit()
            log_audit('ADD_EMPLOYEES_TO_CAMPAIGN', 'campaign', campaign_id,
                     f'Added {added_count} employees')

            if invalid_emails:
                flash(f'Skipped {len(invalid_emails)} invalid emails: {", ".join(invalid_emails[:5])}', 'warning')
            flash(f'Added {added_count} employees to campaign', 'success')
            return redirect(url_for('campaign_detail', campaign_id=campaign_id))
        
        except Exception as e:
            logger.error(f'Error adding employees: {str(e)}')
            flash(f'Error adding employees: {str(e)}', 'error')
    
    return render_template('admin/add_employees.html', campaign=campaign)


@app.route('/admin/campaigns/<campaign_id>/send-emails', methods=['POST'])
@login_required
def send_campaign_emails(campaign_id):
    """Send phishing simulation emails to all employees in campaign."""
    campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
    
    if not campaign or campaign.created_by_id != session['admin_id']:
        return jsonify({'success': False, 'message': 'Campaign not found'}), 404
    
    try:
        campaign_employees = CampaignEmployee.query.filter_by(
            campaign_id=campaign.id,
            status='pending'
        ).all()
        
        sent_count = 0
        failed_count = 0
        
        for ce in campaign_employees:
            employee = Employee.query.get(ce.employee_id)
            
            result = send_phishing_simulation_email(campaign, ce, employee)
            
            if result.get('success'):
                ce.email_sent_at = datetime.utcnow()
                ce.status = 'sent'
                sent_count += 1
            else:
                failed_count += 1
                logger.warning(f'Failed to send email to {employee.email}')
        
        if sent_count > 0:
            campaign.status = 'sent'
        db.session.commit()
        
        log_audit('SEND_CAMPAIGN_EMAILS', 'campaign', campaign_id,
                 f'Sent {sent_count}, Failed {failed_count}')
        
        return jsonify({
            'success': sent_count > 0 or failed_count == 0,
            'message': f'Sent {sent_count} emails, {failed_count} failed',
            'sent': sent_count,
            'failed': failed_count
        })
    
    except Exception as e:
        logger.error(f'Error sending emails: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/admin/campaigns/<campaign_id>/test-email', methods=['POST'])
@login_required
def test_email(campaign_id):
    """Send a test email to a selected recipient or campaign employee."""
    campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
    
    if not campaign or campaign.created_by_id != session['admin_id']:
        return jsonify({'success': False, 'message': 'Campaign not found'}), 404
    
    try:
        admin = Admin.query.get(session['admin_id'])

        payload = request.get_json(silent=True) or {}
        recipient_email = (request.form.get('test_recipient') or payload.get('test_recipient') or '').strip()

        if not recipient_email:
            first_campaign_employee = CampaignEmployee.query.filter_by(campaign_id=campaign.id).first()
            if first_campaign_employee:
                recipient = Employee.query.get(first_campaign_employee.employee_id)
                if recipient and recipient.email:
                    recipient_email = recipient.email

        if not recipient_email:
            recipient_email = admin.email
        
        # Create a test employee record temporarily
        test_token = str(uuid.uuid4())
        base_url = request.host_url.rstrip('/')
        tracking_link = generate_tracking_link(base_url, str(campaign.campaign_id), test_token)
        
        # Generate test email
        from email_service.mailer import generate_html_email, get_email_service
        
        html_content = generate_html_email(
            campaign,
            recipient_email,
            tracking_link,
            campaign.phishing_type
        )
        
        email_service = get_email_service()
        result = email_service.send_email(
            to_email=recipient_email,
            subject=f"[TEST] {campaign.subject_line}",
            html_content=html_content,
            text_content=f"This is a test email. Click here: {tracking_link}"
        )
        
        if result.get('success'):
            log_audit('TEST_EMAIL_SENT', 'campaign', campaign_id,
                     f'Test email sent to {recipient_email}')
            logger.info(f'Test email sent to {recipient_email}')

        result['recipient'] = recipient_email
        result['provider'] = getattr(email_service, 'provider', None)
        result['smtp_host'] = getattr(email_service, 'host', None)
        result['smtp_port'] = getattr(email_service, 'port', None)
        return jsonify(result)
    
    except Exception as e:
        logger.error(f'Error sending test email: {str(e)}', exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/admin/campaigns/<campaign_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_campaign(campaign_id):
    """Edit existing campaign details."""
    campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()

    if not campaign or campaign.created_by_id != session['admin_id']:
        flash('Campaign not found', 'error')
        return redirect(url_for('campaigns_list'))

    templates = get_phishing_templates()

    if request.method == 'POST':
        try:
            campaign.name = request.form.get('name')
            campaign.description = request.form.get('description')

            db.session.commit()

            log_audit('EDIT_CAMPAIGN', 'campaign', campaign_id,
                      f'Campaign: {campaign.name}')
            logger.info(f'Campaign edited: {campaign.name}')

            flash('Campaign updated successfully', 'success')
            return redirect(url_for('campaign_detail', campaign_id=campaign_id))

        except Exception as e:
            logger.error(f'Error editing campaign: {str(e)}')
            flash(f'Error editing campaign: {str(e)}', 'error')

    return render_template('admin/campaign_form.html',
                           templates=templates,
                           campaign=campaign,
                           is_edit=True)


@app.route('/admin/campaigns/<campaign_id>/resend', methods=['GET', 'POST'])
@login_required
def resend_campaign(campaign_id):
    """Resend campaign emails using selected strategy."""
    campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()

    if not campaign or campaign.created_by_id != session['admin_id']:
        flash('Campaign not found', 'error')
        return redirect(url_for('campaigns_list'))

    if request.method == 'POST':
        try:
            resend_option = request.form.get('resend_option', 'unsent')

            if resend_option == 'unsent':
                campaign_employees = CampaignEmployee.query.filter_by(
                    campaign_id=campaign.id,
                    email_sent_at=None
                ).all()
            elif resend_option == 'all':
                campaign_employees = CampaignEmployee.query.filter_by(
                    campaign_id=campaign.id
                ).all()
                for ce in campaign_employees:
                    ce.email_sent_at = None
                    ce.status = 'pending'
            else:
                campaign_employees = CampaignEmployee.query.filter_by(
                    campaign_id=campaign.id,
                    status='pending'
                ).all()

            sent_count = 0
            failed_count = 0

            for ce in campaign_employees:
                employee = Employee.query.get(ce.employee_id)
                result = send_phishing_simulation_email(campaign, ce, employee)

                if result.get('success'):
                    ce.email_sent_at = datetime.utcnow()
                    ce.status = 'sent'
                    sent_count += 1
                else:
                    failed_count += 1
                    logger.warning(f'Failed to resend email to {employee.email}')

            if sent_count > 0:
                campaign.status = 'sent'

            db.session.commit()

            log_audit('RESEND_CAMPAIGN_EMAILS', 'campaign', campaign_id,
                      f'Resent {sent_count}, Failed {failed_count}')

            flash(f'Resent {sent_count} emails, {failed_count} failed', 'success')
            return redirect(url_for('campaign_detail', campaign_id=campaign_id))

        except Exception as e:
            logger.error(f'Error resending campaign: {str(e)}')
            flash(f'Error resending campaign: {str(e)}', 'error')

    campaign_employees = CampaignEmployee.query.filter_by(campaign_id=campaign.id).all()
    unsent_count = sum(1 for ce in campaign_employees if not ce.email_sent_at)
    sent_count = sum(1 for ce in campaign_employees if ce.email_sent_at)

    return render_template(
        'admin/resend_campaign.html',
        campaign=campaign,
        total_employees=len(campaign_employees),
        unsent_count=unsent_count,
        sent_count=sent_count
    )


# ============================================================================
# CLICK TRACKING ROUTES
# ============================================================================

@csrf.exempt
@app.route('/track/click/<campaign_id>/<tracking_token>', methods=['GET'])
def track_click_event(campaign_id, tracking_token):
    """Track phishing link click and redirect to awareness portal."""
    ip_address = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')
    
    # Track the click
    result = track_click(campaign_id, tracking_token, ip_address, user_agent)
    
    if result.get('success'):
        # Redirect to awareness portal
        return redirect(url_for(
            'awareness_portal',
            campaign_id=campaign_id,
            tracking_token=tracking_token
        ))
    else:
        # Invalid link
        return render_template('error.html',
                             title='Invalid Link',
                             message='This link is invalid or has expired.'), 404


@csrf.exempt
@app.route('/track/open/<campaign_id>/<tracking_token>', methods=['GET'])
def track_open_event(campaign_id, tracking_token):
    """Track email open via pixel — does NOT count as a click."""
    try:
        campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
        if campaign:
            campaign_employee = CampaignEmployee.query.filter_by(
                campaign_id=campaign.id,
                tracking_token=tracking_token
            ).first()
            if campaign_employee and not campaign_employee.email_opened:
                campaign_employee.email_opened = True
                db.session.commit()
                logger.info(f'Email opened tracked: campaign={campaign_id}, token={tracking_token}')
    except Exception as e:
        logger.error(f'Error tracking open: {str(e)}')
    
    # Return a transparent 1x1 GIF
    gif = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    from flask import Response
    return Response(gif, mimetype='image/gif')


# ============================================================================
# AWARENESS PORTAL ROUTES
# ============================================================================

@csrf.exempt
@app.route('/awareness/<campaign_id>/<tracking_token>', methods=['GET'])
def awareness_portal(campaign_id, tracking_token):
    """Display phishing awareness training content."""
    try:
        # Find campaign-employee record
        campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
        if not campaign:
            return render_template('error.html',
                                 title='Campaign Not Found',
                                 message='This campaign does not exist.'), 404
        
        campaign_employee = CampaignEmployee.query.filter_by(
            campaign_id=campaign.id,
            tracking_token=tracking_token
        ).first()
        
        if not campaign_employee:
            return render_template('error.html',
                                 title='Invalid Link',
                                 message='This link is not valid.'), 404
        
        employee = Employee.query.get(campaign_employee.employee_id)
        
        return render_template(
            'awareness/portal.html',
            campaign=campaign,
            campaign_employee=campaign_employee,
            employee=employee,
            tracking_token=tracking_token
        )
    
    except Exception as e:
        logger.error(f'Error rendering awareness portal: {str(e)}')
        return render_template('error.html',
                             title='Error',
                             message='An error occurred.'), 500


# ============================================================================
# QUIZ ROUTES
# ============================================================================

@csrf.exempt
@app.route('/quiz/<campaign_id>/<tracking_token>', methods=['GET'])
def quiz_page(campaign_id, tracking_token):
    """Display quiz questions."""
    try:
        campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
        if not campaign:
            return render_template('error.html', title='Campaign Not Found'), 404
        
        campaign_employee = CampaignEmployee.query.filter_by(
            campaign_id=campaign.id,
            tracking_token=tracking_token
        ).first()
        
        if not campaign_employee:
            return render_template('error.html', title='Invalid Link'), 404

        # Prevent quiz replay
        existing_result = QuizResult.query.filter_by(
            campaign_employee_id=campaign_employee.id
        ).first()
        if existing_result:
            return redirect(url_for('quiz_results', tracking_token=tracking_token))
        
        # Get quiz questions
        questions = get_quiz_questions(campaign.phishing_type)
        
        return render_template(
            'quiz/quiz.html',
            campaign=campaign,
            questions=questions,
            tracking_token=tracking_token,
            campaign_id=campaign_id
        )
    
    except Exception as e:
        logger.error(f'Error rendering quiz: {str(e)}')
        return render_template('error.html', title='Error'), 500


@csrf.exempt
@app.route('/api/quiz/submit', methods=['POST'])
def submit_quiz():
    """Submit quiz answers and save results."""
    try:
        data = request.get_json()
        campaign_id = data.get('campaign_id')
        tracking_token = data.get('tracking_token')
        answers = data.get('answers')
        time_taken = data.get('time_taken', 0)
        
        # Find campaign and employee
        campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
        if not campaign:
            return jsonify({'success': False, 'message': 'Campaign not found'}), 404

        campaign_employee = CampaignEmployee.query.filter_by(
            campaign_id=campaign.id,
            tracking_token=tracking_token
        ).first()
        if not campaign_employee:
            return jsonify({'success': False, 'message': 'Invalid tracking token'}), 404
        
        employee = Employee.query.get(campaign_employee.employee_id)
        
        # Save quiz result
        result = save_quiz_result(
            campaign_id,
            employee.employee_id,
            campaign.phishing_type,
            answers,
            time_taken
        )
        
        if result.get('success'):
            # Calculate risk score
            calculate_and_save_risk_score(campaign_employee.id)
            
            log_audit('QUIZ_SUBMITTED', 'quiz', result['result_id'],
                     f'Score: {result["score"]}, Passed: {result["passed"]}',
                     admin_id=None)
            
            return jsonify({
                'success': True,
                'message': 'Quiz submitted successfully',
                'score': result['score'],
                'passed': result['passed'],
                'answers': result['answers']
            })
        
        return jsonify(result), 400
    
    except Exception as e:
        logger.error(f'Error submitting quiz: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/quiz/results/<tracking_token>', methods=['GET'])
def quiz_results(tracking_token):
    """Display quiz results to employee."""
    try:
        campaign_employee = CampaignEmployee.query.filter_by(
            tracking_token=tracking_token
        ).first()
        
        if not campaign_employee:
            return render_template('error.html', title='Not Found'), 404
        
        quiz_result = QuizResult.query.filter_by(
            campaign_employee_id=campaign_employee.id
        ).first()
        
        if not quiz_result:
            return render_template('error.html', title='Results Not Found'), 404
        
        answers = json.loads(quiz_result.answers_json) if quiz_result.answers_json else []
        campaign = Campaign.query.get(quiz_result.campaign_id)
        
        return render_template(
            'quiz/results.html',
            quiz_result=quiz_result,
            answers=answers,
            campaign=campaign
        )
    
    except Exception as e:
        logger.error(f'Error displaying quiz results: {str(e)}')
        return render_template('error.html', title='Error'), 500


# ============================================================================
# ADMIN REPORTS ROUTES
# ============================================================================

@app.route('/admin/reports/click-statistics', methods=['GET'])
@login_required
def click_statistics_report():
    """View click statistics report."""
    campaign_id = request.args.get('campaign_id')
    stats = get_click_statistics(campaign_id)
    
    campaigns = Campaign.query.filter_by(created_by_id=session['admin_id']).all()
    
    return render_template(
        'admin/reports/click_statistics.html',
        stats=stats,
        campaigns=campaigns,
        selected_campaign_id=campaign_id
    )


@app.route('/admin/reports/quiz-analytics', methods=['GET'])
@login_required
def quiz_analytics_report():
    """View quiz analytics report."""
    campaign_id = request.args.get('campaign_id')
    stats = get_quiz_statistics(campaign_id)
    
    campaigns = Campaign.query.filter_by(created_by_id=session['admin_id']).all()
    
    return render_template(
        'admin/reports/quiz_analytics.html',
        stats=stats,
        campaigns=campaigns,
        selected_campaign_id=campaign_id
    )


@app.route('/admin/reports/awareness-report', methods=['GET'])
@login_required
def awareness_report():
    """View employee awareness report."""
    campaign_id = request.args.get('campaign_id')
    
    if campaign_id:
        campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
        if not campaign or campaign.created_by_id != session['admin_id']:
            flash('Campaign not found', 'error')
            return redirect(url_for('admin_dashboard'))
        
        risk_summary = get_campaign_risk_summary(campaign_id)
        dept_analysis = get_department_risk_analysis(campaign_id)
        
        return render_template(
            'admin/reports/awareness_report.html',
            campaign=campaign,
            risk_summary=risk_summary,
            dept_analysis=dept_analysis
        )
    
    campaigns = Campaign.query.filter_by(created_by_id=session['admin_id']).all()
    return render_template(
        'admin/reports/awareness_report.html',
        campaigns=campaigns
    )


# ============================================================================
# API ENDPOINTS FOR AJAX CALLS
# ============================================================================

@app.route('/api/campaigns/<campaign_id>/employees', methods=['GET'])
@login_required
def api_campaign_employees(campaign_id):
    """Get employees and their status for a campaign."""
    campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
    
    if not campaign or campaign.created_by_id != session['admin_id']:
        return jsonify({'success': False, 'message': 'Not authorized'}), 403
    
    campaign_employees = CampaignEmployee.query.filter_by(campaign_id=campaign.id).all()
    
    employees = []
    for ce in campaign_employees:
        employee = Employee.query.get(ce.employee_id)
        risk_score = RiskScore.query.filter_by(campaign_employee_id=ce.id).first()
        
        employees.append({
            'email': employee.email,
            'full_name': employee.full_name,
            'status': ce.status,
            'clicked': ce.clicked,
            'clicked_at': ce.clicked_at.isoformat() if ce.clicked_at else None,
            'awareness_level': risk_score.overall_awareness_level if risk_score else 'unknown',
            'quiz_score': risk_score.quiz_score if risk_score else 0
        })
    
    return jsonify({
        'success': True,
        'employees': employees
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('error.html',
                         title='Page Not Found',
                         message='The page you requested does not exist.'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f'Internal server error: {str(error)}')
    return render_template('error.html',
                         title='Internal Server Error',
                         message='An internal server error occurred.'), 500


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    """Return JSON for API/AJAX CSRF failures, HTML otherwise."""
    wants_json = (
        request.path.startswith('/api/')
        or request.is_json
        or 'application/json' in (request.headers.get('Accept', '') or '').lower()
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    )
    if wants_json:
        return jsonify({'success': False, 'message': f'CSRF validation failed: {error.description}'}), 400

    flash(f'CSRF validation failed: {error.description}', 'error')
    return redirect(url_for('login'))


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

@app.shell_context_processor
def make_shell_context():
    """Flask shell context."""
    return {
        'db': db,
        'Admin': Admin,
        'Campaign': Campaign,
        'Employee': Employee,
        'CampaignEmployee': CampaignEmployee
    }


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


if __name__ == '__main__':
    init_db()
    app.run(
        debug=app.config.get('DEBUG', False),
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', 5000))
    )
