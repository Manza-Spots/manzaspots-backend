"""
Vistas para autenticación OAuth (Google, Facebook, etc.).
"""
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from drf_spectacular.utils import extend_schema
from rest_framework import status
from authentication.base import BaseOAuthView
from authentication.docs.schemas import FACEBOOK, GOOGLE
from authentication.services import AuthenticationService
from authentication.adapters import CustomFacebookOAuth2Adapter
from django.contrib.auth import get_user_model
from authentication.docs.request import GOOGLE_LOGIN_REQUEST, FACEBOOK_LOGIN_REQUEST
from authentication.docs.response import LOGIN_RESPONSE
from allauth.socialaccount.providers.oauth2.client import OAuth2Error

from core.responses.messages import UserMessages

User = get_user_model()

_MODULE_PATH = 'auth.views.oauth_views'


@GOOGLE
class GoogleLoginView(BaseOAuthView, SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = 'http://localhost:8000/accounts/google/login/callback/'
    sentry_operation_name = "google_authentication"
    
    def post(self, request, *args, **kwargs):
        return self.handle_with_sentry(
            operation=self._google_login,
            request=request,
            tags={
                'app': 'authentication',
                'component': 'GoogleLoginView',
                'provider': 'google'
            },
            success_message={'detail': UserMessages.LOGIN},
            success_status=status.HTTP_200_OK
        )
    
    def _google_login(self, request, *args, **kwargs):
            # Llamar al método de la librería
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                user = self.user
                is_new = self._is_new_user(user)
                
                # Verificar email automáticamente
                AuthenticationService.verify_provider_email(user, 'google')
                
                # Setup de nuevo usuario si aplica
                if is_new:
                    AuthenticationService.setup_new_user(user, provider='google')
                
                # Generar tokens en formato consistente
                response.data = self.generate_token_response(user)
                
                # Log del evento
                self.log_auth_event(
                    'google_login',
                    user=user,
                    success=True,
                    is_new_user=is_new
                )
                
            else:
                self.log_auth_event(
                    'google_login_failed',
                    user=None,
                    success=False,
                    provider='google',
                    status_code=response.status_code,
                    reason=response.data.get('detail', 'Unknown') if hasattr(response, 'data') else 'Unknown',
                    ip=request.META.get('REMOTE_ADDR')
                )
        
            
            return response


@FACEBOOK
class FacebookLoginView(BaseOAuthView, SocialLoginView):
    adapter_class = CustomFacebookOAuth2Adapter
    client_class = OAuth2Client
    sentry_operation_name = "facebook_authentication"
    
    def post(self, request, *args, **kwargs):
        return self.handle_with_sentry(
            operation=self._facebook_login,
            request=request,
            tags={
                'app': 'authentication',
                'component': 'FacebookLoginView',
                'provider': 'facebook'
            },
            success_message={'detail': UserMessages.LOGIN},
            success_status=status.HTTP_200_OK
        )
    
    def _facebook_login(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            user = self.user
            is_new = self._is_new_user(user)
            
            # Verificar email automáticamente
            AuthenticationService.verify_provider_email(user, 'facebook')
            
            # Setup de nuevo usuario si aplica
            if is_new:
                AuthenticationService.setup_new_user(user, provider='facebook')
            
            # Generar tokens en formato consistente
            response.data = self.generate_token_response(user)
            
            # Log del evento
            self.log_auth_event(
                'facebook_login',
                user=user,
                success=True,
                is_new_user=is_new
            )
        
        else:
            self.log_auth_event(
                'facebook_login_failed',
                user=None,
                success=False,
                provider='facebook',
                status_code=response.status_code,
                reason=response.data.get('detail', 'Unknown') if hasattr(response, 'data') else 'Unknown',
                ip=request.META.get('REMOTE_ADDR')
            )
        return response