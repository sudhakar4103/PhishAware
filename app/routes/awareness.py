"""
Awareness Blueprint
Handles awareness portal and quiz functionality.
"""

import logging
import json
from flask import Blueprint, render_template, request, jsonify

from database.models import db, Campaign, CampaignEmployee, Employee, QuizResult
from quiz.quiz_engine import get_quiz_questions, save_quiz_result
from detection_engine.risk_scoring import calculate_and_save_risk_score
from app.utils import log_audit

logger = logging.getLogger(__name__)

awareness_bp = Blueprint('awareness', __name__)


@awareness_bp.route('/awareness/<campaign_id>/<tracking_token>', methods=['GET'])
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


@awareness_bp.route('/quiz/<campaign_id>/<tracking_token>', methods=['GET'])
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


@awareness_bp.route('/quiz/results/<tracking_token>', methods=['GET'])
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
