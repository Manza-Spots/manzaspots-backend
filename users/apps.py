from django.apps import AppConfig

class UsersConfig(AppConfig):  # ⚠️ El nombre debe ser UsersConfig, NO MiAppConfig
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users' 
    
    def ready(self):
        """Se ejecuta cuando Django inicia la app"""
        import users.signals  
        from .scheduler import start_scheduler
        start_scheduler()