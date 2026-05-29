"""
Email service for sending phishing simulation emails over Gmail SMTP.
"""

import logging
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys
from pathlib import Path

try:
    import config
except ModuleNotFoundError:
    # Allow running this module directly by adding project root to sys.path.
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    import config


logger = logging.getLogger(__name__)


class EmailService:
    """Base email service class."""
    
    def __init__(self, provider='gmail'):
        """Initialize email service with specified provider."""
        self.provider = provider
        self.sender_email = config.Config.SENDER_EMAIL
        self.sender_name = config.Config.SENDER_NAME
        
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send email - implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement send_email()")


class GmailEmailService(EmailService):
    """Email service using Gmail SMTP."""

    def __init__(self):
        """Initialize Gmail email service."""
        super().__init__('gmail')
        self.host = config.Config.GMAIL_SMTP_HOST
        self.port = config.Config.GMAIL_SMTP_PORT
        self.username = config.Config.GMAIL_USERNAME
        self.password = config.Config.GMAIL_APP_PASSWORD

        if not self.username or not self.password:
            logger.warning('Gmail SMTP credentials not configured')

    def send_email(self, to_email, subject, html_content, text_content=None):
        """
        Send email via Gmail SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)
        
        Returns:
            dict: Success status and message
        """
        try:
            if not self.username or not self.password:
                return {
                    'success': False,
                    'message': 'Gmail SMTP credentials are not configured',
                    'timestamp': datetime.utcnow().isoformat()
                }

            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            from_email = self.sender_email or self.username
            message['From'] = f'{self.sender_name} <{from_email}>'
            message['To'] = to_email
            
            # Add parts
            if text_content:
                message.attach(MIMEText(text_content, 'plain'))
            message.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP(self.host, self.port) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                server.login(self.username, self.password)
                server.sendmail(from_email, [to_email], message.as_string())
            
            logger.info(f'Email sent successfully to {to_email}')
            return {
                'success': True,
                'message': 'Email sent successfully',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except smtplib.SMTPAuthenticationError as e:
            logger.error(
                'SMTP authentication failed for host=%s port=%s user=%s: %s',
                self.host,
                self.port,
                self.username,
                str(e)
            )
            return {
                'success': False,
                'message': (
                    f'SMTP authentication failed on {self.host}:{self.port}. '
                    'Verify the Gmail address and app password.'
                ),
                'timestamp': datetime.utcnow().isoformat()
            }
        except smtplib.SMTPException as e:
            logger.error(f'SMTP error sending to {to_email}: {str(e)}')
            return {
                'success': False,
                'message': f'SMTP error: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            }
        except OSError as e:
            logger.error(f'Network/DNS error connecting to SMTP host {self.host}:{self.port}: {str(e)}')
            return {
                'success': False,
                'message': (
                    f'Network error connecting to SMTP host {self.host}:{self.port}. '
                    f'Please verify Gmail SMTP settings and network DNS access. ({str(e)})'
                ),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f'Unexpected error sending to {to_email}: {str(e)}')
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
    return GmailEmailService()


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
    click_link = tracking_link
    
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
        from flask import current_app
        
        # Get email service
        email_service = get_email_service()
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
