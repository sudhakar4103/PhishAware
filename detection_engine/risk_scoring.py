"""
Risk Scoring Module for PhishAware

Handles risk score calculation and analysis for phishing simulation campaigns.
Provides functions to calculate individual risk scores and generate campaign/department-level analytics.
"""

from .detection_engine import (
    calculate_and_save_risk_score,
    get_campaign_risk_summary,
    get_department_risk_analysis
)

__all__ = [
    'calculate_and_save_risk_score',
    'get_campaign_risk_summary',
    'get_department_risk_analysis'
]
