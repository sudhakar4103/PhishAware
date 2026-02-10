"""
Click tracking system for phishing simulation links.
Captures and logs all click events with metadata.
"""

import logging
import uuid
import re
from datetime import datetime

from database.models import db, ClickTracking, CampaignEmployee, Campaign, Employee


logger = logging.getLogger(__name__)


def generate_tracking_token():
    """
    Generate unique tracking token for campaign-employee combination.
    
    Returns:
        str: UUID-based tracking token
    """
    return str(uuid.uuid4())


def parse_device_info(user_agent):
    """
    Parse device and browser information from User-Agent header.
    
    Args:
        user_agent: User-Agent string from request header
    
    Returns:
        dict: Parsed browser and device information
    """
    try:
        ua_lower = user_agent.lower() if user_agent else ''
        
        # Browser detection
        browser = 'Unknown'
        browser_version = ''
        
        if 'chrome' in ua_lower:
            browser = 'Chrome'
            match = re.search(r'Chrome/([0-9.]+)', user_agent)
            browser_version = match.group(1) if match else ''
        elif 'safari' in ua_lower and 'chrome' not in ua_lower:
            browser = 'Safari'
            match = re.search(r'Version/([0-9.]+)', user_agent)
            browser_version = match.group(1) if match else ''
        elif 'firefox' in ua_lower:
            browser = 'Firefox'
            match = re.search(r'Firefox/([0-9.]+)', user_agent)
            browser_version = match.group(1) if match else ''
        elif 'edge' in ua_lower:
            browser = 'Edge'
            match = re.search(r'Edg/([0-9.]+)', user_agent)
            browser_version = match.group(1) if match else ''
        
        # OS detection
        os = 'Unknown'
        if 'windows' in ua_lower:
            os = 'Windows'
        elif 'mac' in ua_lower:
            os = 'macOS'
        elif 'linux' in ua_lower:
            os = 'Linux'
        elif 'iphone' in ua_lower or 'ipad' in ua_lower:
            os = 'iOS'
        elif 'android' in ua_lower:
            os = 'Android'
        
        return {
            'browser': browser,
            'browser_version': browser_version,
            'os': os
        }
    except Exception as e:
        logger.warning(f'Error parsing user agent: {str(e)}')
        return {
            'browser': 'Unknown',
            'os': 'Unknown'
        }


def get_device_type(user_agent):
    """
    Determine device type (desktop, mobile, tablet) from User-Agent.
    
    Args:
        user_agent: User-Agent string
    
    Returns:
        str: Device type
    """
    ua_lower = user_agent.lower() if user_agent else ''
    
    if 'mobile' in ua_lower or 'android' in ua_lower:
        return 'mobile'
    elif 'ipad' in ua_lower or 'tablet' in ua_lower:
        return 'tablet'
    else:
        return 'desktop'


def track_click(campaign_id, tracking_token, ip_address, user_agent):
    """
    Record a click event on a phishing simulation link.
    
    Args:
        campaign_id: Campaign UUID or ID
        tracking_token: Unique employee tracking token
        ip_address: IP address of the clicker
        user_agent: User-Agent string from browser
    
    Returns:
        dict: Click tracking result with status and details
    """
    try:
        # Find campaign
        campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
        if not campaign:
            logger.warning(f'Campaign not found: {campaign_id}')
            return {'success': False, 'message': 'Campaign not found', 'status_code': 404}
        
        # Find campaign-employee record
        campaign_employee = CampaignEmployee.query.filter_by(
            campaign_id=campaign.id,
            tracking_token=tracking_token
        ).first()
        
        if not campaign_employee:
            logger.warning(f'Tracking token not found: {tracking_token}')
            return {'success': False, 'message': 'Invalid tracking link', 'status_code': 404}
        
        # Check if already clicked
        if campaign_employee.clicked:
            logger.info(f'Re-click detected for campaign {campaign_id}, token {tracking_token}')
            return {
                'success': True,
                'message': 'Click already recorded',
                'campaign_id': campaign_id,
                'already_clicked': True
            }
        
        # Get employee
        employee = Employee.query.get(campaign_employee.employee_id)
        
        # Parse device info
        device_info = parse_device_info(user_agent)
        device_type = get_device_type(user_agent)
        
        # Create click tracking record
        click_tracking = ClickTracking(
            click_id=str(uuid.uuid4()),
            campaign_id=campaign.id,
            employee_id=employee.id,
            campaign_employee_id=campaign_employee.id,
            clicked_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            browser_info=f"{device_info.get('browser', 'Unknown')} {device_info.get('browser_version', '')}",
            device_type=device_type
        )
        
        # Update campaign-employee record
        campaign_employee.clicked = True
        campaign_employee.clicked_at = datetime.utcnow()
        campaign_employee.status = 'clicked'
        
        # Add to database
        db.session.add(click_tracking)
        db.session.commit()
        
        logger.info(
            f'Click tracked successfully - Campaign: {campaign_id}, '
            f'Employee: {employee.email}, IP: {ip_address}'
        )
        
        return {
            'success': True,
            'message': 'Click recorded successfully',
            'campaign_id': campaign_id,
            'employee_email': employee.email,
            'clicked_at': click_tracking.clicked_at.isoformat(),
            'click_id': click_tracking.click_id,
            'device_type': device_type
        }
    
    except Exception as e:
        logger.error(f'Error tracking click: {str(e)}')
        db.session.rollback()
        return {'success': False, 'message': f'Error: {str(e)}', 'status_code': 500}


def get_click_statistics(campaign_id=None, employee_id=None):
    """
    Get click statistics for reporting.
    
    Args:
        campaign_id: Optional campaign ID to filter
        employee_id: Optional employee ID to filter
    
    Returns:
        dict: Click statistics and metrics
    """
    try:
        query = ClickTracking.query
        
        if campaign_id:
            campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
            if campaign:
                query = query.filter_by(campaign_id=campaign.id)
        
        if employee_id:
            employee = Employee.query.filter_by(employee_id=employee_id).first()
            if employee:
                query = query.filter_by(employee_id=employee.id)
        
        clicks = query.all()
        
        device_breakdown = {}
        browser_breakdown = {}
        
        for click in clicks:
            device_breakdown[click.device_type] = device_breakdown.get(click.device_type, 0) + 1
            browser = click.browser_info.split()[0] if click.browser_info else 'Unknown'
            browser_breakdown[browser] = browser_breakdown.get(browser, 0) + 1
        
        return {
            'total_clicks': len(clicks),
            'device_breakdown': device_breakdown,
            'browser_breakdown': browser_breakdown,
            'clicks': [
                {
                    'click_id': click.click_id,
                    'clicked_at': click.clicked_at.isoformat(),
                    'device_type': click.device_type,
                    'browser': click.browser_info
                }
                for click in clicks
            ]
        }
    
    except Exception as e:
        logger.error(f'Error getting click statistics: {str(e)}')
        return {'success': False, 'message': f'Error: {str(e)}'}


def get_employee_click_details(employee_id, campaign_id=None):
    """
    Get detailed click information for an employee.
    
    Args:
        employee_id: Employee ID
        campaign_id: Optional campaign ID to filter
    
    Returns:
        dict: Employee click details
    """
    try:
        employee = Employee.query.filter_by(employee_id=employee_id).first()
        if not employee:
            return {'success': False, 'message': 'Employee not found'}
        
        query = ClickTracking.query.filter_by(employee_id=employee.id)
        
        if campaign_id:
            campaign = Campaign.query.filter_by(campaign_id=campaign_id).first()
            if campaign:
                query = query.filter_by(campaign_id=campaign.id)
        
        clicks = query.all()
        
        return {
            'employee_email': employee.email,
            'total_clicks': len(clicks),
            'clicks': [
                {
                    'campaign_id': click.campaign.campaign_id,
                    'campaign_name': click.campaign.name,
                    'clicked_at': click.clicked_at.isoformat(),
                    'device_type': click.device_type,
                    'browser': click.browser_info,
                    'ip_address': click.ip_address
                }
                for click in clicks
            ]
        }
    
    except Exception as e:
        logger.error(f'Error getting employee click details: {str(e)}')
        return {'success': False, 'message': f'Error: {str(e)}'}
