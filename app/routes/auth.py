"""
Authentication BlueprintVersion: 1.0.0
Handles user login and logout functionality.
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash

from database.models import db, Admin
from app.utils import log_audit

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/', methods=['GET'])
def index():
    """Home page redirects to login or dashboard."""
    if 'admin_id' in session:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.is_active and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            admin.last_login = datetime.utcnow()
            db.session.commit()
            
            log_audit('LOGIN_SUCCESS', 'admin', admin.id)
            logger.info(f'Admin {username} logged in successfully')
            
            return redirect(url_for('admin.dashboard'))
        
        log_audit('LOGIN_FAILED', 'admin', None, f'Failed login attempt: {username}')
        flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Admin logout."""
    admin_id = session.get('admin_id')
    if admin_id:
        log_audit('LOGOUT', 'admin', admin_id)
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))
