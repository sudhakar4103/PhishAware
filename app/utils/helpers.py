"""
Helper utilities for PhishAware application.Version: 1.0.0"""

import uuid
import logging
from flask import request, session
from database.models import db, AuditLog

logger = logging.getLogger(__name__)


def get_client_ip():
    """Get client IP address from request."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr


def log_audit(action, resource_type, resource_id, details=None, admin_id=None):
    """Log audit event."""
    try:
        audit = AuditLog(
            log_id=str(uuid.uuid4()),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            admin_id=admin_id or session.get('admin_id'),
            details=details,
            ip_address=get_client_ip()
        )
        db.session.add(audit)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error logging audit: {str(e)}")
