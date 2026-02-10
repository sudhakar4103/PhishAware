"""
Database models for PhishAware Platform.
Defines tables for campaigns, employees, clicks, quiz results, and admin users.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Admin(db.Model):
    """Admin user model for platform administration."""
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    campaigns = db.relationship('Campaign', backref='created_by', lazy='dynamic')
    
    def __repr__(self):
        return f'<Admin {self.username}>'


class Campaign(db.Model):
    """Phishing simulation campaign model."""
    __tablename__ = 'campaign'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    sender_name = db.Column(db.String(120), nullable=False)
    sender_email = db.Column(db.String(120), nullable=False)
    subject_line = db.Column(db.String(255), nullable=False)
    phishing_type = db.Column(db.String(50), nullable=False)  # e.g., 'credential_harvesting', 'malware', 'urgent_action'
    email_template = db.Column(db.Text, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, sent, completed
    is_active = db.Column(db.Boolean, default=True)
    
    employees = db.relationship('CampaignEmployee', backref='campaign', lazy='dynamic', cascade='all, delete-orphan')
    clicks = db.relationship('ClickTracking', backref='campaign', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Campaign {self.name}>'


class Employee(db.Model):
    """Employee model for training participants."""
    __tablename__ = 'employee'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    campaign_employees = db.relationship('CampaignEmployee', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    clicks = db.relationship('ClickTracking', backref='employee', lazy='dynamic')
    quiz_results = db.relationship('QuizResult', backref='employee', lazy='dynamic')
    
    def __repr__(self):
        return f'<Employee {self.email}>'


class CampaignEmployee(db.Model):
    """Junction table linking campaigns and employees."""
    __tablename__ = 'campaign_employee'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    tracking_token = db.Column(db.String(128), unique=True, nullable=False, index=True)
    email_sent_at = db.Column(db.DateTime, nullable=True)
    email_opened = db.Column(db.Boolean, default=False)
    clicked = db.Column(db.Boolean, default=False)
    clicked_at = db.Column(db.DateTime, nullable=True)
    awareness_level = db.Column(db.String(20), default='unknown')  # low, medium, high, unknown
    status = db.Column(db.String(20), default='pending')  # pending, sent, clicked, completed
    
    __table_args__ = (db.UniqueConstraint('campaign_id', 'employee_id', name='uq_campaign_employee'),)
    
    def __repr__(self):
        return f'<CampaignEmployee campaign={self.campaign_id}, employee={self.employee_id}>'


class ClickTracking(db.Model):
    """Track every click event on phishing simulation links."""
    __tablename__ = 'click_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    click_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    campaign_employee_id = db.Column(db.Integer, db.ForeignKey('campaign_employee.id'), nullable=False)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.Text, nullable=True)
    browser_info = db.Column(db.String(255), nullable=True)
    device_type = db.Column(db.String(50), nullable=True)  # desktop, mobile, tablet
    location = db.Column(db.String(255), nullable=True)
    
    __table_args__ = (db.Index('idx_campaign_employee', 'campaign_id', 'employee_id'),)
    
    def __repr__(self):
        return f'<ClickTracking campaign={self.campaign_id}, employee={self.employee_id}>'


class QuizResult(db.Model):
    """Store quiz results for each employee."""
    __tablename__ = 'quiz_result'
    
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    campaign_employee_id = db.Column(db.Integer, db.ForeignKey('campaign_employee.id'), nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)  # percentage
    time_taken = db.Column(db.Integer, nullable=False)  # seconds
    passed = db.Column(db.Boolean, nullable=False)
    answers_json = db.Column(db.Text, nullable=True)  # JSON string of all answers
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<QuizResult employee={self.employee_id}, score={self.score}>'


class RiskScore(db.Model):
    """Calculated risk and awareness scores for each employee per campaign."""
    __tablename__ = 'risk_score'
    
    id = db.Column(db.Integer, primary_key=True)
    score_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    campaign_employee_id = db.Column(db.Integer, db.ForeignKey('campaign_employee.id'), nullable=False)
    
    # Risk factors
    clicked_link = db.Column(db.Boolean, default=False)
    click_time_minutes = db.Column(db.Integer, nullable=True)  # Minutes to click after email sent
    
    # Awareness scores
    quiz_score = db.Column(db.Float, default=0)  # 0-100
    overall_awareness_level = db.Column(db.String(20), default='low')  # low, medium, high
    risk_level = db.Column(db.String(20), default='high')  # low, medium, high
    
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<RiskScore employee={self.employee_id}, awareness={self.overall_awareness_level}>'


class AuditLog(db.Model):
    """Audit log for security and compliance tracking."""
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # campaign, employee, quiz, etc.
    resource_id = db.Column(db.String(100), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.action}>'
