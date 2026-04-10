"""
Utility functions and custom exception handlers
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """Custom exception handler for REST framework"""
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response = {
            'error': str(exc),
            'code': exc.__class__.__name__,
            'status': response.status_code
        }
        response.data = custom_response
    
    return response


def admin_required(view_func):
    """Decorator to require admin role"""
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        if request.user.role.role_name != 'admin':
            return Response({'error': 'Admin access required'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper
