from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

def cleanup_unverified_users():
    """Elimina usuarios no verificados después de 7 días"""
    try:
        expiration_date = timezone.now() - timedelta(days=7)
        
        users_to_delete = User.objects.filter(
            is_active=False,
            last_login__isnull=True,
            date_joined__lt=expiration_date
        )
        
        count = users_to_delete.count()
        emails = list(users_to_delete.values_list('email', flat=True)[:10])
        
        users_to_delete.delete()
        
        logger.info(
            f'Limpieza automática: {count} usuarios no verificados eliminados. '
            f'Ejemplos: {emails}'
        )
        
        return count
        
    except Exception as e:
        logger.error(f'Error en cleanup_unverified_users: {str(e)}')
        raise
