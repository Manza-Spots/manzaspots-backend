import re
import unicodedata
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomFacebookOAuth2Adapter(FacebookOAuth2Adapter):
    """Adaptador profesional con generación de username único garantizado"""
    
    def complete_login(self, request, app, token, **kwargs):
        login = super().complete_login(request, app, token, **kwargs)
        
        extra_data = login.account.extra_data        
        # Solo generar username si el usuario es nuevo o no tiene username válido
        if login.user and (not login.user.pk or not login.user.username or login.user.username.strip() == ''):
            username = self._generate_unique_username(extra_data, User)
            login.user.username = username
        
        return login
    
    def _generate_unique_username(self, data, User):
        """
        Genera un username único garantizado.
        """
        base_username = self._get_base_username_from_name(data)
        
        if not base_username:
            email = data.get('email', '')
            if email and '@' in email:
                base_username = email.split('@')[0]
                base_username = self._sanitize_username(base_username)
        
        if not base_username:
            return f"fb{data.get('id', 'user')}"
        
        return self._ensure_unique_username(base_username, User)
    
    def _get_base_username_from_name(self, data):
        """Extrae y sanitiza el nombre para usar como base del username"""
        name = data.get('name', '').strip()
        if name:
            username = self._sanitize_username(name)
            if username:
                return username
        
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        if first_name or last_name:
            full_name = f"{first_name}{last_name}".strip()
            username = self._sanitize_username(full_name)
            if username:
                return username
        
        return None
    
    def _sanitize_username(self, name):
        """
        Sanitiza el nombre para convertirlo en username válido:
        - Normaliza Unicode (á→a, ñ→n)
        - Solo letras y números
        - Minúsculas
        - Máximo 30 caracteres (dejamos espacio para sufijos)
        """
        username = unicodedata.normalize('NFKD', name)
        username = username.encode('ascii', 'ignore').decode('ascii')
        
        username = username.lower()
        username = re.sub(r'[^a-z0-9]', '', username)
        
        username = username[:30]
        
        return username if username else None
    
    def _ensure_unique_username(self, base_username, User):
        """
        Garantiza que el username sea único agregando sufijo numérico.
        """
        username = base_username
        
        if not User.objects.filter(username=username).exists():
            return username
        
        counter = 1
        max_attempts = 9999  
        
        while counter < max_attempts:
            username = f"{base_username}{counter}"
            
            if not User.objects.filter(username=username).exists():
                return username
            
            counter += 1
        
        import time
        return f"{base_username}{int(time.time())}"