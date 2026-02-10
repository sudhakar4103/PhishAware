"""
Email service for sending phishing simulation emails.
Supports Mailtrap and SendGrid as email providers.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import uuid

from config import Config


logger = logging.getLogger(__name__)


class EmailService:
    """Base email service class."""
    
    def __init__(self, provider='mailtrap'):
        """Initialize email service with specified provider."""
        self.provider = provider
        self.sender_email = Config.SENDER_EMAIL
        self.sender_name = Config.SENDER_NAME
        
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send email - implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement send_email()")


class MailtrapEmailService(EmailService):
    """Email service using Mailtrap SMTP server."""
    
    def __init__(self):
        """Initialize Mailtrap email service."""
        super().__init__('mailtrap')
        self.host = Config.MAILTRAP_HOST
        self.port = Config.MAILTRAP_PORT
        self.username = Config.MAILTRAP_USERNAME
        self.password = Config.MAILTRAP_PASSWORD
        
        if not self.username or not self.password:
            logger.warning('Mailtrap credentials not configured')
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """
        Send email via Mailtrap SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)
        
        Returns:
            dict: Success status and message
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f'{self.sender_name} <{self.sender_email}>'
            message['To'] = to_email
            
            # Add parts
            if text_content:
                message.attach(MIMEText(text_content, 'plain'))
            message.attach(MIMEText(html_content, 'html'))
            
            # Send via Mailtrap
            with smtplib.SMTP_SSL(self.host, self.port) as server:
                server.login(self.username, self.password)
                server.sendmail(self.sender_email, to_email, message.as_string())
            
            logger.info(f'Email sent successfully to {to_email}')
            return {
                'success': True,
                'message': 'Email sent successfully',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except smtplib.SMTPException as e:
            logger.error(f'SMTP error sending to {to_email}: {str(e)}')
            return {
                'success': False,
                'message': f'SMTP error: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f'Unexpected error sending to {to_email}: {str(e)}')
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }


class SendGridEmailService(EmailService):
    """Email service using SendGrid API."""
    
    def __init__(self):
        """Initialize SendGrid email service."""
        super().__init__('sendgrid')
        self.api_key = Config.SENDGRID_API_KEY
        
        if not self.api_key:
            logger.warning('SendGrid API key not configured')
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """
        Send email via SendGrid API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)
        
        Returns:
            dict: Success status and message
        """
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            message = Mail(
                from_email=Email(self.sender_email, self.sender_name),
                to_emails=To(to_email),
                subject=subject,
                plain_text_content=text_content or 'Please view this email in HTML mode',
                html_content=html_content
            )
            
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            logger.info(f'Email sent via SendGrid to {to_email}: Status {response.status_code}')
            
            return {
                'success': response.status_code in [200, 201, 202],
                'message': 'Email sent successfully',
                'status_code': response.status_code,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except ImportError:
            logger.error('SendGrid library not installed')
            return {
                'success': False,
                'message': 'SendGrid library not installed',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f'SendGrid error: {str(e)}')
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }


def get_email_service():
    """
    Factory function to get appropriate email service.
    
    Returns:
        EmailService: Configured email service instance
    """
    provider = Config.EMAIL_PROVIDER.lower()
    
    if provider == 'sendgrid':
        return SendGridEmailService()
    else:  # Default to Mailtrap
        return MailtrapEmailService()


def generate_tracking_link(base_url, campaign_id, tracking_token):
    """
    Generate unique tracking link for employee.
    
    Args:
        base_url: Base URL of the application
        campaign_id: Campaign identifier
        tracking_token: Unique token for this employee in this campaign
    
    Returns:
        str: Complete tracking URL
    """
    return f"{base_url}/track/click/{campaign_id}/{tracking_token}"


def generate_html_email(campaign, employee_email, tracking_link, phishing_type):
    """
    Generate HTML email content for phishing simulation.
    
    Args:
        campaign: Campaign object
        employee_email: Employee email address
        tracking_link: Generated tracking link
        phishing_type: Type of phishing attack
    
    Returns:
        str: HTML email content
    """
    # Pixel tracker for email open tracking
    pixel_tracker = f'<img src="{tracking_link}?action=open" width="1" height="1" alt="" />'
    
    # Create click link with tracker
    click_link = f'{tracking_link}?action=click'
    
    template_html = campaign.email_template or ''
    template_html = template_html.replace('{{tracking_link}}', click_link)
    template_html = template_html.replace('{{ tracking_link }}', click_link)
    template_html = template_html.replace('{{TRACKING_LINK}}', click_link)

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto;">
            {template_html}
            <p style="margin-top: 20px; font-size: 12px; color: #999;">
                <em>Training Disclaimer: This is a simulation for authorized security awareness training only.</em>
            </p>
        </div>
        {pixel_tracker}
    </body>
    </html>
    """
    
    return html_content


def send_phishing_simulation_email(campaign, campaign_employee, employee):
    """
    Send phishing simulation email to employee.
    
    Args:
        campaign: Campaign object
        campaign_employee: CampaignEmployee object
        employee: Employee object
    
    Returns:
        dict: Result of email sending
    """
    try:
        from tracking.click_tracker import generate_tracking_token
        from flask import url_for, current_app
        
        # Generate tracking token
        tracking_token = campaign_employee.tracking_token
        
        # Generate tracking link
        base_url = current_app.config.get('SERVER_URL', 'http://localhost:5000')
        tracking_link = generate_tracking_link(base_url, str(campaign.campaign_id), tracking_token)
        
        # Generate email HTML
        html_content = generate_html_email(
            campaign,
            employee.email,
            tracking_link,
            campaign.phishing_type
        )
        
        # Get email service
        email_service = get_email_service()
        
        # Send email
        result = email_service.send_email(
            to_email=employee.email,
            subject=campaign.subject_line,
            html_content=html_content,
            text_content=campaign.subject_line
        )
        
        # Log the attempt
        if result['success']:
            logger.info(
                f'Phishing simulation email sent to {employee.email} '
                f'for campaign {campaign.name}'
            )
        else:
            logger.error(
                f'Failed to send phishing simulation email to {employee.email}: '
                f'{result.get("message", "Unknown error")}'
            )
        
        return result
    
    except Exception as e:
        logger.error(f'Error in send_phishing_simulation_email: {str(e)}')
        return {
            'success': False,
            'message': f'Error: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }
