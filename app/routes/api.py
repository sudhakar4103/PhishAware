"""
API Blueprint
Handles JSON API endpoints for AJAX calls.
"""

import logging
from flask import Blueprint, jsonify, session, request

from database.models import db, Campaign, CampaignEmployee, Employee, RiskScore, QuizResult
from app.utils import login_required, log_audit
from quiz.quiz_engine import save_quiz_result
from detection_engine.risk_scoring import calculate_and_save_risk_score

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


@api_bp.route('/campaigns/<campaign_id>/employees', methods=['GET'])
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


@api_bp.route('/quiz/submit', methods=['POST'])
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
