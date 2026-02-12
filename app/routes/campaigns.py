"""
Campaigns Blueprint
Handles campaign CRUD operations and email sending.
"""

import logging
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify

from database.models import db, Campaign, Employee, CampaignEmployee, Admin
from app.utils import login_required, log_audit
from phishing_templates import get_phishing_templates, get_phishing_template_by_id
from detection_engine.risk_scoring import get_campaign_risk_summary
from email_service.mailer import (
    get_email_service, send_phishing_simulation_email, 
    generate_tracking_link, generate_html_email
)

logger = logging.getLogger(__name__)

campaigns_bp = Blueprint('campaigns', __name__)


@campaigns_bp.route('/', methods=['GET'])
@login_required
def campaigns_list():
    """List all campaigns for admin."""
    admin = Admin.query.get(session['admin_id'])
    campaigns = Campaign.query.filter_by(created_by_id=admin.id).order_by(Campaign.created_at.desc()).all()
    
    return render_template('admin/campaigns.html', campaigns=campaigns)


@campaigns_bp.route('/create', methods=['GET', 'POST'])
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
            return redirect(url_for('campaigns.campaign_detail', campaign_id=campaign.campaign_id))
        
        except Exception as e:
            logger.error(f'Error creating campaign: {str(e)}')
            flash(f'Error creating campaign: {str(e)}', 'error')
    
    return render_template('admin/campaign_form.html', templates=templates)


@campaigns_bp.route('/<campaign_id>', methods=['GET'])
@login_required
def campaign_detail(campaign_id):
    """View campaign details and statistics."""
    campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
    
    if not campaign or campaign.created_by_id != session['admin_id']:
        flash('Campaign not found', 'error')
        return redirect(url_for('campaigns.campaigns_list'))
    
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


@campaigns_bp.route('/<campaign_id>/add-employees', methods=['GET', 'POST'])
@login_required
def add_employees_to_campaign(campaign_id):
    """Add employees to campaign."""
    campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
    
    if not campaign or campaign.created_by_id != session['admin_id']:
        flash('Campaign not found', 'error')
        return redirect(url_for('campaigns.campaigns_list'))
    
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
            return redirect(url_for('campaigns.campaign_detail', campaign_id=campaign_id))
        
        except Exception as e:
            logger.error(f'Error adding employees: {str(e)}')
            flash(f'Error adding employees: {str(e)}', 'error')
    
    return render_template('admin/add_employees.html', campaign=campaign)


@campaigns_bp.route('/<campaign_id>/send-emails', methods=['POST'])
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


@campaigns_bp.route('/<campaign_id>/test-email', methods=['POST'])
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
