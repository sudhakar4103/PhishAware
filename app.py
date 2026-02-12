
"""PhishAware - Phishing Awareness Training Platform
Version: 1.0.0
Date: February 12, 2026
"""
__version__ = '1.0.0'

import os
import logging
from datetime import datetime
import uuid
import json

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

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

# Initialize database
db.init_app(app)

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
            flash('Please log in first', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_client_ip():
    """Get client IP address from request."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
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
    campaigns = Campaign.query.filter_by(created_by_id=admin.id).all()
    
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
    campaigns = Campaign.query.filter_by(created_by_id=admin.id).order_by(Campaign.created_at.desc()).all()
    
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
            
            added_count = 0
            for email in email_list:
                email = email.strip()
                if not email:
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
    """Send a test email to admin's email to verify email configuration."""
    campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
    
    if not campaign or campaign.created_by_id != session['admin_id']:
        return jsonify({'success': False, 'message': 'Campaign not found'}), 404
    
    try:
        admin = Admin.query.get(session['admin_id'])
        
        # Create a test employee record temporarily
        test_token = str(uuid.uuid4())
        base_url = request.host_url.rstrip('/')
        tracking_link = generate_tracking_link(base_url, str(campaign.campaign_id), test_token)
        
        # Generate test email
        from email_service.mailer import generate_html_email, get_email_service
        
        html_content = generate_html_email(
            campaign,
            admin.email,
            tracking_link,
            campaign.phishing_type
        )
        
        email_service = get_email_service()
        result = email_service.send_email(
            to_email=admin.email,
            subject=f"[TEST] {campaign.subject_line}",
            html_content=html_content,
            text_content=f"This is a test email. Click here: {tracking_link}"
        )
        
        if result.get('success'):
            log_audit('TEST_EMAIL_SENT', 'campaign', campaign_id,
                     f'Test email sent to {admin.email}')
            logger.info(f'Test email sent to {admin.email}')
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f'Error sending test email: {str(e)}', exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================================
# CLICK TRACKING ROUTES
# ============================================================================

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


# ============================================================================
# AWARENESS PORTAL ROUTES
# ============================================================================

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
        campaign_employee = CampaignEmployee.query.filter_by(
            campaign_id=campaign.id,
            tracking_token=tracking_token
        ).first()
        
        if not campaign or not campaign_employee:
            return jsonify({'success': False, 'message': 'Invalid campaign or employee'}), 404
        
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
    app.run(debug=True, host='0.0.0.0', port=5000)
