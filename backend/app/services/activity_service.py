"""
Activity logging service
"""
import json
from datetime import datetime
from ..models import ActivityLog


def log_activity(user, action_type, details=None):
    """Log user activity"""
    if details and not isinstance(details, str):
        details = json.dumps(details)
    
    ActivityLog.objects.create(
        user=user,
        action_type=action_type,
        details=details
    )


def log_error(user, error_type, details):
    """Log error activity"""
    log_activity(
        user=user,
        action_type='error',
        details=json.dumps({
            'error_type': error_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    )
