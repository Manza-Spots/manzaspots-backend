# spots_routes/apps.py
from django.apps import AppConfig

class SpotsRoutesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'spots_routes'
    
    def ready(self):
        import spots_routes.signals  