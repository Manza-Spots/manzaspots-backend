"""
Clases base que TODAS las vistas de autenticación heredarán.
Esto garantiza comportamiento consistente.
"""
import json
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from core.mixins import SentryErrorHandlerMixin
from manza_spots.throttling import SensitiveOperationThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class BaseAuthenticationView(SentryErrorHandlerMixin):
    """
    Clase base para TODAS las vistas de autenticación.
    
    Proporciona:
    - Manejo de errores con Sentry
    - Throttling consistente
    - Logging estandarizado
    - Formato de respuesta unificado
    """
    permission_classes = [AllowAny]
    throttle_classes = [SensitiveOperationThrottle]
    
    def log_auth_event(self, event_type, user=None, success=True, **extra):
        """
        Log centralizado de eventos de autenticación.
        
        Args:
            event_type: Tipo de evento (login, register, password_reset, etc.)
            user: Usuario involucrado (si existe)
            success: Si la operación fue exitosa
            **extra: Datos adicionales para el log
        """
        log_data = {
            'event_type': event_type,
            'success': success,
            'timestamp': timezone.now().isoformat(),
            **extra
        }
        
        if user:
            log_data.update({
                'user_id': user.id,
                'user_email': user.email,
                'is_new_user': self._is_new_user(user)
            })
        
        message = f"[bold cyan]{event_type}[/bold cyan]: {user.email if user else 'N/A'}"
        details = json.dumps(log_data, indent=2, default=str)
        
        if success:
            logger.info(f"{message}\n{details}", extra={'log_data': log_data})
        else:
            logger.warning(f"{message}\n{details}", extra={'log_data': log_data})
            
    def _is_new_user(self, user):
        """Detecta si el usuario fue creado recientemente (últimos 10 segundos)"""
        return user.date_joined > timezone.now() - timedelta(seconds=10)
    
    def generate_token_response(self, user):
        """
        Genera respuesta estándar con tokens JWT.
        
        TODAS las vistas de autenticación retornan el mismo formato.
        """
        refresh = RefreshToken.for_user(user)
        
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }


class BaseJWTView(BaseAuthenticationView):
    """
    Clase base específica para vistas JWT.
    Extiende BaseAuthenticationView con funcionalidad JWT.
    """
    pass


class BaseOAuthView(BaseAuthenticationView):
    """
    Clase base específica para vistas OAuth.
    Extiende BaseAuthenticationView con funcionalidad OAuth.
    """
    
    def verify_email_from_provider(self, user):
        """
        Marca automáticamente como verificado el email de proveedores confiables.
        Google y Facebook ya verifican emails, no necesitamos hacerlo de nuevo.
        """
        if hasattr(user, 'emailaddress_set'):
            from allauth.account.models import EmailAddress
            
            EmailAddress.objects.update_or_create(
                user=user,
                email=user.email,
                defaults={
                    'verified': True,
                    'primary': True
                }
            )
            
            self.log_auth_event(
                'email_verified_from_provider',
                user=user,
                provider=self.__class__.__name__
            )