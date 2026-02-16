"""
Servicios de lógica de negocio para autenticación.
TODA la lógica de negocio va aquí, NO en las vistas.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.exceptions import ValidationError
import logging
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from itsdangerous import URLSafeTimedSerializer

from core.services.email_service import PasswordResetEmail

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthenticationService:
    """
    Servicio centralizado para operaciones de autenticación.
    
    Ventajas:
    - Reutilizable en diferentes vistas
    - Testeable independientemente
    - Lógica de negocio separada de HTTP
    """
    
    @staticmethod
    def generate_tokens_for_user(user):
        """Genera tokens JWT para un usuario"""
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
    
    @staticmethod
    def verify_provider_email(user, provider_name):
        """
        Verifica automáticamente el email de proveedores OAuth confiables.
        
        Args:
            user: Usuario a verificar
            provider_name: Nombre del proveedor (google, facebook, etc.)
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
            
            logger.info(
                f"Email auto-verified from {provider_name}",
                extra={'user_id': user.id, 'provider': provider_name}
            )
    
    @staticmethod
    def setup_new_user(user, provider=None):
        """
        Configuración inicial para nuevos usuarios.
        
        Args:
            user: Usuario recién creado
            provider: Proveedor de autenticación (opcional)
        """
        # Aquí puedes agregar lógica adicional:
        # - Crear perfil de usuario
        # - Asignar roles por defecto
        # - Enviar email de bienvenida
        # - Crear configuraciones iniciales
        
        logger.info(
            f"New user setup completed",
            extra={
                'user_id': user.id,
                'provider': provider or 'local',
                'email_verified': user.emailaddress_set.filter(verified=True).exists() if hasattr(user, 'emailaddress_set') else False
            }
        )

class PasswordResetService:
    """
    Servicio para restablecimiento de contraseña.
    """
    
    @staticmethod
    def request_reset(email, request):
        """Solicita un restablecimiento de contraseña"""
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)
            
            reset_path = f"/auth/reset-password/{uid}/{token}/"
            reset_url = request.build_absolute_uri(reset_path)
            
            PasswordResetEmail.send_email(user.email, reset_url = reset_url, nombre = user.username)
            
            logger.info(f"Restablecimiento de contraseña enviado a: {email}")
            
        except User.DoesNotExist:
            logger.warning(f"No existe un usuario con el correo: {email}")
    
    @staticmethod
    def confirm_reset(uidb64, token, new_password):
        """Confirma y ejecuta el restablecimiento de contraseña"""
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            logger.warning(f"Invalid uidb64 attempt: {uidb64}")
            raise ValidationError('Token inválido o expirado.')
        
        if not PasswordResetTokenGenerator().check_token(user, token):
            logger.warning(f"Invalid token for user {user.email}")
            raise ValidationError('Token inválido o expirado.')
        
        user.set_password(new_password)
        user.save()
        logger.info(f"Password reset successful for {user.email}")
        
        return user
    
class UsersRegisterService:
    @staticmethod
    def generate_email_token(user, new_email=None):
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        payload = {'user_id': user.id}
        if new_email:
            payload['new_email'] = new_email
        return serializer.dumps(payload, salt='email-confirm')

    @staticmethod
    def verify_email_token(token, max_age=3600):
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        try:
            data = serializer.loads(token, salt='email-confirm', max_age=max_age)
            return data  
        except Exception:
            return None

    @staticmethod
    def get_confirmation_url(user, request, new_email=None):
        token = UsersRegisterService.generate_email_token(user, new_email)
        verify_url = f"/users/verify-email?token={token}"
        return request.build_absolute_uri(verify_url)