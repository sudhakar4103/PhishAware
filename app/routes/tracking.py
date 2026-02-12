"""
Tracking Blueprint
Handles click tracking for phishing links.
"""

import logging
from flask import Blueprint, redirect, url_for, render_template, request

from tracking.click_tracker import track_click
from app.utils import get_client_ip

logger = logging.getLogger(__name__)

tracking_bp = Blueprint('tracking', __name__)


@tracking_bp.route('/click/<campaign_id>/<tracking_token>', methods=['GET'])
def track_click_event(campaign_id, tracking_token):
    """Track phishing link click and redirect to awareness portal."""
    ip_address = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')
    
    # Track the click
    result = track_click(campaign_id, tracking_token, ip_address, user_agent)
    
    if result.get('success'):
        # Redirect to awareness portal
        return redirect(url_for(
            'awareness.awareness_portal',
            campaign_id=campaign_id,
            tracking_token=tracking_token
        ))
    else:
        # Invalid link
        return render_template('error.html',
                             title='Invalid Link',
                             message='This link is invalid or has expired.'), 404
