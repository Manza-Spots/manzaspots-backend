from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Elimina usuarios no verificados después de X días'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Días antes de eliminar usuarios no verificados'
        )

    def handle(self, *args, **options):
        days = options['days']
        expiration_date = timezone.now() - timedelta(days=days)
        
        unverified_users = User.objects.filter(
            is_active=False,
            last_login__isnull=True,
            date_joined__lt=expiration_date
        )
        
        count = unverified_users.count()
        emails = list(unverified_users.values_list('email', flat=True))
        
        unverified_users.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Eliminados {count} usuarios no verificados: {emails}'
            )
        )