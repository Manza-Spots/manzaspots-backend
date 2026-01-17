from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled

def custom_exception_handler(exc, context):
    """Manejador de errores para rate limiting."""
    response = exception_handler(exc, context)
    
    if isinstance(exc, Throttled):
        custom_response_data = {
            'error': 'rate_limit_exceeded',
            'message': 'Has excedido el límite de peticiones permitidas.',
            'detail': 'Por favor, espera antes de intentar nuevamente.',
            'retry_after_seconds': int(exc.wait) if exc.wait else 60,
        }
        response.data = custom_response_data
        response['Retry-After'] = int(exc.wait) if exc.wait else 60
    
    return response