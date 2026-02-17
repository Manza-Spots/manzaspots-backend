from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

class EmailService:
    @classmethod
    def send_template_email(cls, subject, to_email, template_name, **context):
        """
        Envía un correo basado en una plantilla HTML.
        Permite pasar cualquier cantidad de variables al contexto.
        
        Ejemplo de uso:
            send_template_email(
                subject='Restablecer contraseña',
                to_email=user.email,
                template_name='emails/reset_password.html',
                user=user,
                reset_url='http://localhost:8000/auth/reset-password/...'
            )
        """
        try: 
            html_content = render_to_string(template_name, context)
            plain_message = strip_tags(html_content) 
            
            result = send_mail(
                subject,
                plain_message,
                'noreply@tuapp.com',
                [to_email],
                html_message=html_content
            )
            
            return result == 1
            
        except Exception as e:
            logger.exception(f"Error al enviar correo a {to_email}: {e}")
            return False

class PasswordResetEmail:
    @staticmethod
    def send_email(to_email, **context):
        subject = "Restablecimiento de contraseña"
        template_name = 'emails/password_reset.html'
        EmailService.send_template_email(subject, to_email, template_name, **context)
        
class ConfirmUserEmail:
    @staticmethod
    def send_email(to_email, **context):
        subject = "Confirmacion de cuenta"
        template_name = 'emails/confirm_email.html'
        EmailService.send_template_email(subject, to_email, template_name, **context)  

class UpdateUserEmail:
    @staticmethod
    def send_email(to_email, **context):
        subject = "Confirmacion de cuenta"
        template_name = 'emails/update_email.html'
        EmailService.send_template_email(subject, to_email, template_name, **context)  