# services.py - Lógica de negocio
import logging
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.forms import ValidationError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from core.services.email_service import PasswordResetEmail

logger = logging.getLogger(__name__)

class PasswordResetService():
    
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