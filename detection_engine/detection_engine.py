"""
Risk scoring and awareness level calculation engine.Version: 1.0.0
Analyzes email behavior and quiz performance to determine awareness levels.
"""

import logging
import uuid
from datetime import datetime
from database.models import db, RiskScore, CampaignEmployee, Campaign, Employee, QuizResult

logger = logging.getLogger(__name__)


def calculate_and_save_risk_score(campaign_employee_id):
    """
    Calculate and save risk score for a campaign employee.
    
    Args:
        campaign_employee_id: ID of CampaignEmployee record
    
    Returns:
        dict: Calculation results
    """
    try:
        campaign_employee = CampaignEmployee.query.get(campaign_employee_id)
        if not campaign_employee:
            return {'success': False, 'message': 'Campaign employee not found'}
        
        # Get quiz result
        quiz_result = QuizResult.query.filter_by(
            campaign_employee_id=campaign_employee_id
        ).first()
        
        quiz_score = quiz_result.score if quiz_result else 0
        clicked = campaign_employee.clicked
        
        # Calculate awareness level
        if clicked:
            awareness_level = 'low'
            risk_level = 'high'
        elif quiz_score >= 80:
            awareness_level = 'high'
            risk_level = 'low'
        elif quiz_score >= 50:
            awareness_level = 'medium'
            risk_level = 'medium'
        else:
            awareness_level = 'low'
            risk_level = 'high'
        
        # Save or update risk score
        risk_score = RiskScore.query.filter_by(
            campaign_employee_id=campaign_employee_id
        ).first()
        
        if not risk_score:
            risk_score = RiskScore(
                score_id=str(uuid.uuid4()),
                campaign_id=campaign_employee.campaign_id,
                employee_id=campaign_employee.employee_id,
                campaign_employee_id=campaign_employee_id
            )
            db.session.add(risk_score)
        
        risk_score.clicked_link = clicked
        risk_score.quiz_score = quiz_score
        risk_score.overall_awareness_level = awareness_level
        risk_score.risk_level = risk_level
        risk_score.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(
            f'Risk score calculated for campaign_employee {campaign_employee_id}: '
            f'awareness={awareness_level}, risk={risk_level}'
        )
        
        return {
            'success': True,
            'awareness_level': awareness_level,
            'risk_level': risk_level,
            'quiz_score': quiz_score
        }
    
    except Exception as e:
        logger.error(f'Error calculating risk score: {str(e)}')
        return {'success': False, 'message': str(e)}


def get_campaign_risk_summary(campaign_id):
    """
    Get risk and awareness summary for a campaign.
    
    Args:
        campaign_id: Campaign ID
    
    Returns:
        dict: Risk summary statistics
    """
    try:
        campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
        if not campaign:
            return {}
        
        risk_scores = RiskScore.query.filter_by(campaign_id=campaign.id).all()
        
        if not risk_scores:
            return {
                'total_employees': 0,
                'high_awareness': 0,
                'medium_awareness': 0,
                'low_awareness': 0,
                'high_risk': 0,
                'medium_risk': 0,
                'low_risk': 0,
                'average_quiz_score': 0,
                'click_rate_percentage': 0
            }
        
        total = len(risk_scores)
        high_awareness = sum(1 for rs in risk_scores if rs.overall_awareness_level == 'high')
        medium_awareness = sum(1 for rs in risk_scores if rs.overall_awareness_level == 'medium')
        low_awareness = sum(1 for rs in risk_scores if rs.overall_awareness_level == 'low')
        
        high_risk = sum(1 for rs in risk_scores if rs.risk_level == 'high')
        medium_risk = sum(1 for rs in risk_scores if rs.risk_level == 'medium')
        low_risk = sum(1 for rs in risk_scores if rs.risk_level == 'low')
        
        avg_quiz = sum(rs.quiz_score for rs in risk_scores) / total if total > 0 else 0
        clicked = sum(1 for rs in risk_scores if rs.clicked_link)
        click_rate = (clicked / total * 100) if total > 0 else 0
        
        return {
            'total_employees': total,
            'high_awareness': high_awareness,
            'medium_awareness': medium_awareness,
            'low_awareness': low_awareness,
            'high_awareness_percentage': round((high_awareness / total * 100), 2) if total > 0 else 0,
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk,
            'average_quiz_score': round(avg_quiz, 2),
            'click_rate_percentage': round(click_rate, 2)
        }
    
    except Exception as e:
        logger.error(f'Error getting campaign risk summary: {str(e)}')
        return {}


def get_department_risk_analysis(campaign_id):
    """
    Get risk analysis broken down by department.
    
    Args:
        campaign_id: Campaign ID
    
    Returns:
        dict: Department-level analysis
    """
    try:
        campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
        if not campaign:
            return {}
        
        risk_scores = RiskScore.query.filter_by(campaign_id=campaign.id).all()
        
        dept_data = {}
        for rs in risk_scores:
            employee = Employee.query.get(rs.employee_id)
            dept = getattr(employee, 'department', None) or 'Unknown'
            
            if dept not in dept_data:
                dept_data[dept] = {
                    'total': 0,
                    'clicked': 0,
                    'high_awareness': 0,
                    'medium_awareness': 0,
                    'low_awareness': 0
                }
            
            dept_data[dept]['total'] += 1
            if rs.clicked_link:
                dept_data[dept]['clicked'] += 1
            
            if rs.overall_awareness_level == 'high':
                dept_data[dept]['high_awareness'] += 1
            elif rs.overall_awareness_level == 'medium':
                dept_data[dept]['medium_awareness'] += 1
            else:
                dept_data[dept]['low_awareness'] += 1
        
        return {
            'departments': dept_data,
            'total_departments': len(dept_data)
        }
    
    except Exception as e:
        logger.error(f'Error getting department risk analysis: {str(e)}')
        return {}