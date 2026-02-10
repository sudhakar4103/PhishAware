"""
Quiz engine for phishing awareness assessment.
Manages quiz questions, scoring, and result tracking.
"""

import logging
import uuid
import json
from datetime import datetime

from database.models import db, QuizResult, CampaignEmployee, Campaign, Employee


logger = logging.getLogger(__name__)


# Quiz questions database
QUIZ_QUESTIONS = {
    'credential_harvesting': [
        {
            'id': 'q1',
            'question': 'What should you do if you receive an unexpected email asking to verify your password?',
            'options': [
                'Click the link immediately to avoid account lockout',
                'Never click links in emails - go directly to the official website',
                'Reply with your password to confirm your identity',
                'Forward the email to someone else to handle'
            ],
            'correct_answer': 1,
            'explanation': 'Legitimate organizations never ask for passwords via email. Always navigate directly to the official website by typing the URL yourself.'
        },
        {
            'id': 'q2',
            'question': 'Which of the following is a RED FLAG in a phishing email?',
            'options': [
                'Formal greeting with your correct name',
                'Urgent language and threats of account closure',
                'Professional company logo and formatting',
                'Request to update profile information through official website'
            ],
            'correct_answer': 1,
            'explanation': 'Urgent language and threats are common phishing tactics to create panic and bypass rational thinking.'
        },
        {
            'id': 'q3',
            'question': 'What should you do before clicking any link in an email?',
            'options': [
                'Just click it - if it breaks something, IT will fix it',
                'Hover over the link to check if the URL matches the sender\'s domain',
                'Click it only if the email looks professional',
                'Wait for your colleague to click it first'
            ],
            'correct_answer': 1,
            'explanation': 'Hovering over links reveals the actual URL destination, which may differ from the displayed text in phishing emails.'
        },
        {
            'id': 'q4',
            'question': 'You receive an email claiming to be from your bank asking to verify account details. What is the safest action?',
            'options': [
                'Call your bank using the number on your debit card',
                'Click the link to verify immediately',
                'Reply to the email with your account details',
                'Simply delete the email'
            ],
            'correct_answer': 0,
            'explanation': 'Contact the organization directly using official contact information to verify any requests.'
        },
        {
            'id': 'q5',
            'question': 'Which email address is a RED FLAG for phishing?',
            'options': [
                'info@company.com',
                'support@company.com',
                'noreply@compny-supp0rt.com',
                'hr@company.com'
            ],
            'correct_answer': 2,
            'explanation': 'Misspelled domain names (compny instead of company, numbers replacing letters) are common in phishing attempts.'
        }
    ],
    'malware': [
        {
            'id': 'q1',
            'question': 'What is the safest approach to email attachments from unknown senders?',
            'options': [
                'Open them to see what they are',
                'Never open attachments from unknown senders without verification',
                'Only open if it\'s a .doc file',
                'Open if your antivirus is running'
            ],
            'correct_answer': 1,
            'explanation': 'Malware can be disguised in various file types. Always verify the sender\'s identity before opening attachments.'
        },
        {
            'id': 'q2',
            'question': 'Which file type is SAFEST to receive as an attachment?',
            'options': [
                '.exe files',
                '.pdf files (if carefully verified)',
                '.zip files',
                'All attachments are equally risky'
            ],
            'correct_answer': 1,
            'explanation': 'While PDFs are generally safer, they can still contain malware. Always verify the sender and use caution.'
        },
        {
            'id': 'q3',
            'question': 'You receive an email with an attachment claiming to be an invoice. The sender is unknown. What should you do?',
            'options': [
                'Open it immediately',
                'Contact IT security before opening',
                'Ask a colleague if they sent it',
                'Delete it without opening'
            ],
            'correct_answer': 1,
            'explanation': 'When in doubt, contact IT security. They can verify the attachment\'s safety.'
        },
        {
            'id': 'q4',
            'question': 'What is a macro and why is it a security concern?',
            'options': [
                'A keyboard shortcut - not a security concern',
                'Automated scripts that can perform actions - they can be malicious',
                'A type of virus that only affects old computers',
                'A setting in Microsoft Word'
            ],
            'correct_answer': 1,
            'explanation': 'Macros are programs that can perform unauthorized actions. Disable macro prompts and be cautious when enabling them.'
        },
        {
            'id': 'q5',
            'question': 'What should you do if your computer starts acting strangely after opening an email attachment?',
            'options': [
                'Ignore it and hope it goes away',
                'Disconnect from the network and contact IT immediately',
                'Try to fix it yourself with downloaded tools',
                'Restart your computer and continue working'
            ],
            'correct_answer': 1,
            'explanation': 'Isolate your device immediately to prevent malware spread. Contact IT security right away.'
        }
    ],
    'urgent_action': [
        {
            'id': 'q1',
            'question': 'A CEO emails asking you to urgently process a wire transfer. What should you do?',
            'options': [
                'Process it immediately to avoid delaying business',
                'Verify the request through another official communication channel before processing',
                'Ask colleagues if they\'ve received similar requests',
                'Process it since it\'s from the CEO'
            ],
            'correct_answer': 1,
            'explanation': 'Always verify urgent financial requests through established channels, even if they appear to come from leadership.'
        },
        {
            'id': 'q2',
            'question': 'Which is a common psychological technique used in phishing attacks?',
            'options': [
                'Making requests very clear and transparent',
                'Giving you plenty of time to decide',
                'Creating urgency and fear to bypass careful thinking',
                'Being honest about the request\'s purpose'
            ],
            'correct_answer': 2,
            'explanation': 'Phishers create artificial urgency to pressure victims into bypassing security checks.'
        },
        {
            'id': 'q3',
            'question': 'You receive an urgent email asking to confirm your login credentials due to "suspicious activity." What is the red flag?',
            'options': [
                'The email is from IT',
                'The sender is urgent',
                'Legitimate companies never ask for passwords via email',
                'The email mentions suspicious activity'
            ],
            'correct_answer': 2,
            'explanation': 'No legitimate organization asks for passwords via email, regardless of the reason or urgency.'
        },
        {
            'id': 'q4',
            'question': 'An email says your account will be closed in 24 hours if you don\'t take action. What should you do?',
            'options': [
                'Act immediately by clicking the link',
                'Contact the organization directly using contact info you find independently',
                'Wait 24 hours to see if your account is actually closed',
                'Forward the email to all colleagues'
            ],
            'correct_answer': 1,
            'explanation': 'Verify urgent threats independently. Legitimate organizations never shut down accounts without proper warning through verified channels.'
        },
        {
            'id': 'q5',
            'question': 'What is the best defense against urgency-based phishing attacks?',
            'options': [
                'Work faster to respond quickly',
                'Take time to verify before acting, even under pressure',
                'Assume emails from authority figures are legitimate',
                'Only trust emails that sound urgent'
            ],
            'correct_answer': 1,
            'explanation': 'Pausing to verify information is the strongest defense against urgency-based social engineering.'
        }
    ]
}


def get_quiz_questions(phishing_type):
    """
    Get quiz questions based on phishing type.
    
    Args:
        phishing_type: Type of phishing (credential_harvesting, malware, urgent_action)
    
    Returns:
        list: Quiz questions without answers
    """
    questions = QUIZ_QUESTIONS.get(phishing_type, QUIZ_QUESTIONS['credential_harvesting'])
    
    # Return questions without correct answers for display
    return [
        {
            'id': q['id'],
            'question': q['question'],
            'options': q['options']
        }
        for q in questions
    ]


def validate_quiz_answer(answer_data, phishing_type):
    """
    Validate quiz answers and calculate score.
    
    Args:
        answer_data: Dict with question_id -> selected_answer_index
        phishing_type: Type of phishing
    
    Returns:
        dict: Scoring results
    """
    try:
        questions = QUIZ_QUESTIONS.get(phishing_type, QUIZ_QUESTIONS['credential_harvesting'])
        
        results = {
            'total_questions': len(questions),
            'correct_answers': 0,
            'answers': []
        }
        
        for question in questions:
            q_id = question['id']
            selected = answer_data.get(q_id)
            correct = question['correct_answer']
            
            is_correct = selected == correct
            if is_correct:
                results['correct_answers'] += 1
            
            results['answers'].append({
                'question_id': q_id,
                'question': question['question'],
                'selected_answer': selected,
                'correct_answer': correct,
                'is_correct': is_correct,
                'explanation': question['explanation']
            })
        
        # Calculate percentage score
        results['score'] = (results['correct_answers'] / results['total_questions']) * 100
        results['passed'] = results['score'] >= 70  # 70% is passing score
        
        logger.info(
            f'Quiz scored: Total={results["total_questions"]}, '
            f'Correct={results["correct_answers"]}, Score={results["score"]:.1f}%'
        )
        
        return results
    
    except Exception as e:
        logger.error(f'Error validating quiz: {str(e)}')
        return {'success': False, 'message': f'Error: {str(e)}'}


def save_quiz_result(campaign_id, employee_id, phishing_type, answer_data, time_taken):
    """
    Save quiz result to database.
    
    Args:
        campaign_id: Campaign UUID
        employee_id: Employee UUID
        phishing_type: Type of phishing
        answer_data: Dict of answers
        time_taken: Time taken in seconds
    
    Returns:
        dict: Saved quiz result
    """
    try:
        # Validate answers
        validation = validate_quiz_answer(answer_data, phishing_type)
        
        if 'error' in validation:
            return validation
        
        # Get campaign and employee
        campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
        employee = Employee.query.filter_by(employee_id=employee_id).first()
        
        if not campaign or not employee:
            return {'success': False, 'message': 'Campaign or employee not found'}
        
        # Get campaign-employee record
        campaign_employee = CampaignEmployee.query.filter_by(
            campaign_id=campaign.id,
            employee_id=employee.id
        ).first()
        
        if not campaign_employee:
            return {'success': False, 'message': 'Enrollment not found'}
        
        # Create quiz result
        quiz_result = QuizResult(
            result_id=str(uuid.uuid4()),
            campaign_id=campaign.id,
            employee_id=employee.id,
            campaign_employee_id=campaign_employee.id,
            total_questions=validation['total_questions'],
            correct_answers=validation['correct_answers'],
            score=validation['score'],
            time_taken=time_taken,
            passed=validation['passed'],
            answers_json=json.dumps(validation['answers']),
            completed_at=datetime.utcnow()
        )
        
        # Update campaign-employee status
        campaign_employee.status = 'completed'
        
        db.session.add(quiz_result)
        db.session.commit()
        
        logger.info(
            f'Quiz result saved: Employee {employee.email}, '
            f'Score {validation["score"]:.1f}%, Passed={validation["passed"]}'
        )
        
        return {
            'success': True,
            'result_id': quiz_result.result_id,
            'score': validation['score'],
            'passed': validation['passed'],
            'total_questions': validation['total_questions'],
            'correct_answers': validation['correct_answers'],
            'answers': validation['answers']
        }
    
    except Exception as e:
        logger.error(f'Error saving quiz result: {str(e)}')
        db.session.rollback()
        return {'success': False, 'message': f'Error: {str(e)}'}


def get_quiz_statistics(campaign_id=None):
    """
    Get aggregated quiz statistics.
    
    Args:
        campaign_id: Optional campaign ID to filter
    
    Returns:
        dict: Quiz statistics
    """
    try:
        query = QuizResult.query
        
        if campaign_id:
            campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
            if campaign:
                query = query.filter_by(campaign_id=campaign.id)
        
        results = query.all()
        
        if not results:
            return {
                'total_attempts': 0,
                'average_score': 0,
                'passing_rate': 0,
                'total_employees': 0
            }
        
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        avg_score = sum(r.score for r in results) / total
        avg_time = sum(r.time_taken for r in results) / total
        
        return {
            'total_attempts': total,
            'average_score': round(avg_score, 2),
            'passing_rate': round((passed / total) * 100, 2),
            'employees_passed': passed,
            'employees_failed': total - passed,
            'average_time_seconds': round(avg_time, 2)
        }
    
    except Exception as e:
        logger.error(f'Error getting quiz statistics: {str(e)}')
        return {'success': False, 'message': f'Error: {str(e)}'}
