from django.apps import AppConfig

class UsersConfig(AppConfig):  # ⚠️ El nombre debe ser UsersConfig, NO MiAppConfig
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'  # ✅ Este es el nombre de tu app
    
    def ready(self):
        """Se ejecuta cuando Django inicia la app"""
        import users.signals  # ✅ Importa tus signals