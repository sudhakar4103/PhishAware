"""
Admin BlueprintVersion: 1.0.0
Handles admin dashboard and reports.
"""

import logging
from flask import Blueprint, render_template, request, session, redirect, url_for, flash

from database.models import Admin, Campaign
from app.utils import login_required
from tracking.click_tracker import get_click_statistics
from quiz.quiz_engine import get_quiz_statistics
from detection_engine.risk_scoring import get_campaign_risk_summary, get_department_risk_analysis

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
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


@admin_bp.route('/reports/click-statistics', methods=['GET'])
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


@admin_bp.route('/reports/quiz-analytics', methods=['GET'])
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


@admin_bp.route('/reports/awareness-report', methods=['GET'])
@login_required
def awareness_report():
    """View employee awareness report."""
    campaign_id = request.args.get('campaign_id')
    
    if campaign_id:
        campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
        if not campaign or campaign.created_by_id != session['admin_id']:
            flash('Campaign not found', 'error')
            return redirect(url_for('admin.dashboard'))
        
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
