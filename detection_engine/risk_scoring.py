"""
Risk scoring and awareness level calculation engine.
Evaluates employee behavior and security awareness.
"""

import logging
import uuid
import json
from datetime import datetime, timedelta

from database.models import (
    db, RiskScore, CampaignEmployee, Campaign, Employee,
    ClickTracking, QuizResult
)
from config import Config


logger = logging.getLogger(__name__)


class RiskScoringEngine:
    """Calculate risk and awareness scores based on employee behavior."""
    
    def __init__(self):
        """Initialize risk scoring engine."""
        self.awareness_high_threshold = Config.AWARENESS_LEVEL_HIGH
        self.awareness_medium_threshold = Config.AWARENESS_LEVEL_MEDIUM
    
    def calculate_email_risk(self, campaign_employee):
        """
        Calculate risk based on email interaction.
        
        Args:
            campaign_employee: CampaignEmployee object
        
        Returns:
            dict: Email risk factors
        """
        risk_factors = {
            'clicked_link': campaign_employee.clicked,
            'click_time_minutes': None,
            'time_to_click_risk': 0  # 0-30 points
        }
        
        if campaign_employee.clicked and campaign_employee.clicked_at and campaign_employee.email_sent_at:
            time_diff = campaign_employee.clicked_at - campaign_employee.email_sent_at
            minutes = time_diff.total_seconds() / 60
            risk_factors['click_time_minutes'] = int(minutes)
            
            # Faster click = higher risk (less thinking time)
            if minutes < 1:
                risk_factors['time_to_click_risk'] = 30
            elif minutes < 5:
                risk_factors['time_to_click_risk'] = 25
            elif minutes < 30:
                risk_factors['time_to_click_risk'] = 20
            elif minutes < 60:
                risk_factors['time_to_click_risk'] = 15
            else:
                risk_factors['time_to_click_risk'] = 10
        
        return risk_factors
    
    def calculate_quiz_awareness_score(self, campaign_employee):
        """
        Calculate awareness score from quiz results.
        
        Args:
            campaign_employee: CampaignEmployee object
        
        Returns:
            float: Quiz-based awareness score (0-100)
        """
        quiz_result = QuizResult.query.filter_by(
            campaign_employee_id=campaign_employee.id
        ).first()
        
        if not quiz_result:
            return 0
        
        return quiz_result.score
    
    def calculate_overall_awareness(self, email_risk, quiz_score):
        """
        Calculate overall awareness level.
        
        Args:
            email_risk: Risk factors from email interaction
            quiz_score: Quiz-based awareness score
        
        Returns:
            dict: Overall awareness metrics
        """
        # Weighted calculation: 40% quiz, 60% email behavior
        # Lower score = better awareness (less clicking)
        
        email_behavior_score = 100
        
        if email_risk['clicked_link']:
            email_behavior_score = 60 - email_risk['time_to_click_risk']
        
        overall_score = (quiz_score * 0.4) + (email_behavior_score * 0.6)
        overall_score = max(0, min(100, overall_score))  # Clamp between 0-100
        
        # Determine awareness level
        if overall_score >= self.awareness_high_threshold:
            awareness_level = 'high'
        elif overall_score >= self.awareness_medium_threshold:
            awareness_level = 'medium'
        else:
            awareness_level = 'low'
        
        return {
            'overall_score': round(overall_score, 2),
            'awareness_level': awareness_level,
            'quiz_contribution': round(quiz_score * 0.4, 2),
            'behavior_contribution': round(email_behavior_score * 0.6, 2)
        }
    
    def calculate_risk_level(self, email_risk, awareness_metrics):
        """
        Calculate overall risk level for employee.
        
        Args:
            email_risk: Risk factors from email
            awareness_metrics: Awareness calculation results
        
        Returns:
            str: Risk level (low, medium, high)
        """
        awareness_score = awareness_metrics['overall_score']
        
        # Risk inversely correlates with awareness
        if awareness_score >= 75:
            return 'low'
        elif awareness_score >= 50:
            return 'medium'
        else:
            return 'high'
    
    def calculate_score(self, campaign_employee):
        """
        Calculate complete risk and awareness score.
        
        Args:
            campaign_employee: CampaignEmployee object
        
        Returns:
            dict: Complete scoring results
        """
        try:
            # Calculate email risk
            email_risk = self.calculate_email_risk(campaign_employee)
            
            # Calculate quiz awareness
            quiz_score = self.calculate_quiz_awareness_score(campaign_employee)
            
            # Calculate overall awareness
            awareness_metrics = self.calculate_overall_awareness(email_risk, quiz_score)
            
            # Calculate risk level
            risk_level = self.calculate_risk_level(email_risk, awareness_metrics)
            
            return {
                'success': True,
                'email_risk': email_risk,
                'quiz_score': quiz_score,
                'awareness_metrics': awareness_metrics,
                'risk_level': risk_level,
                'assessed_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f'Error calculating score: {str(e)}')
            return {'success': False, 'message': f'Error: {str(e)}'}


def calculate_and_save_risk_score(campaign_employee_id):
    """
    Calculate and save risk score for a campaign-employee combination.
    
    Args:
        campaign_employee_id: ID of CampaignEmployee record
    
    Returns:
        dict: Saved risk score
    """
    try:
        campaign_employee = CampaignEmployee.query.get(campaign_employee_id)
        if not campaign_employee:
            return {'success': False, 'message': 'Campaign employee not found'}
        
        # Calculate score
        engine = RiskScoringEngine()
        scoring = engine.calculate_score(campaign_employee)
        
        if not scoring.get('success', True):
            return scoring
        
        # Create or update risk score record
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
        
        # Update risk score fields
        risk_score.clicked_link = scoring['email_risk']['clicked_link']
        risk_score.click_time_minutes = scoring['email_risk']['click_time_minutes']
        risk_score.quiz_score = scoring['quiz_score']
        risk_score.overall_awareness_level = scoring['awareness_metrics']['awareness_level']
        risk_score.risk_level = scoring['risk_level']
        risk_score.updated_at = datetime.utcnow()
        
        db.session.add(risk_score)
        db.session.commit()
        
        logger.info(
            f'Risk score calculated and saved: '
            f'Campaign {campaign_employee.campaign_id}, '
            f'Employee {campaign_employee.employee_id}, '
            f'Awareness={risk_score.overall_awareness_level}'
        )
        
        return {
            'success': True,
            'score_id': risk_score.score_id,
            'awareness_level': risk_score.overall_awareness_level,
            'risk_level': risk_score.risk_level,
            'quiz_score': risk_score.quiz_score
        }
    
    except Exception as e:
        logger.error(f'Error calculating and saving risk score: {str(e)}')
        db.session.rollback()
        return {'success': False, 'message': f'Error: {str(e)}'}


def get_campaign_risk_summary(campaign_id):
    """
    Get risk summary for entire campaign.
    
    Args:
        campaign_id: Campaign UUID
    
    Returns:
        dict: Campaign-wide risk metrics
    """
    try:
        campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
        if not campaign:
            return {'success': False, 'message': 'Campaign not found'}
        
        # Get all risk scores for this campaign
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
                'click_rate': 0,
                'average_awareness_score': 0
            }
        
        total = len(risk_scores)
        high_awareness = sum(1 for r in risk_scores if r.overall_awareness_level == 'high')
        medium_awareness = sum(1 for r in risk_scores if r.overall_awareness_level == 'medium')
        low_awareness = sum(1 for r in risk_scores if r.overall_awareness_level == 'low')
        
        high_risk = sum(1 for r in risk_scores if r.risk_level == 'high')
        medium_risk = sum(1 for r in risk_scores if r.risk_level == 'medium')
        low_risk = sum(1 for r in risk_scores if r.risk_level == 'low')
        
        clicked = sum(1 for r in risk_scores if r.clicked_link)
        avg_quiz_score = sum(r.quiz_score for r in risk_scores) / total
        
        return {
            'total_employees': total,
            'high_awareness': high_awareness,
            'medium_awareness': medium_awareness,
            'low_awareness': low_awareness,
            'high_awareness_percentage': round((high_awareness / total) * 100, 2),
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk,
            'click_rate_percentage': round((clicked / total) * 100, 2),
            'average_quiz_score': round(avg_quiz_score, 2)
        }
    
    except Exception as e:
        logger.error(f'Error getting campaign risk summary: {str(e)}')
        return {'success': False, 'message': f'Error: {str(e)}'}


def get_department_risk_analysis(campaign_id, department=None):
    """
    Get risk analysis by department.
    
    Args:
        campaign_id: Campaign UUID
        department: Optional specific department
    
    Returns:
        dict: Department-level risk metrics
    """
    try:
        campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
        if not campaign:
            return {'success': False, 'message': 'Campaign not found'}
        
        # Get employees for this campaign
        campaign_employees = CampaignEmployee.query.filter_by(
            campaign_id=campaign.id
        ).all()
        
        departments = {}
        
        for ce in campaign_employees:
            employee = Employee.query.get(ce.employee_id)
            dept = employee.department or 'Unknown'
            
            if department and dept != department:
                continue
            
            if dept not in departments:
                departments[dept] = {
                    'employees': [],
                    'total': 0,
                    'clicked': 0,
                    'high_awareness': 0,
                    'medium_awareness': 0,
                    'low_awareness': 0
                }
            
            risk_score = RiskScore.query.filter_by(
                campaign_employee_id=ce.id
            ).first()
            
            dept_data = departments[dept]
            dept_data['total'] += 1
            
            if ce.clicked:
                dept_data['clicked'] += 1
            
            if risk_score:
                if risk_score.overall_awareness_level == 'high':
                    dept_data['high_awareness'] += 1
                elif risk_score.overall_awareness_level == 'medium':
                    dept_data['medium_awareness'] += 1
                else:
                    dept_data['low_awareness'] += 1
            
            dept_data['employees'].append({
                'email': employee.email,
                'clicked': ce.clicked,
                'awareness': risk_score.overall_awareness_level if risk_score else 'unknown',
                'quiz_score': risk_score.quiz_score if risk_score else 0
            })
        
        return {
            'campaign_id': campaign_id,
            'departments': departments
        }
    
    except Exception as e:
        logger.error(f'Error getting department risk analysis: {str(e)}')
        return {'success': False, 'message': f'Error: {str(e)}'}
