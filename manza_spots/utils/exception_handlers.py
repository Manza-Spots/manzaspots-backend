from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    Manejador de excepciones personalizado que envuelve todo en 'detail'
    Solo para errores (status >= 400)
    """
    response = exception_handler(exc, context)
    
    if response is not None and response.status_code >= 400:
        if isinstance(response.data, dict) and 'detail' in response.data and len(response.data) == 1:
            response.data = {'detail': response.data['detail']}
        else:
            response.data = {'detail': response.data}
    
    return response