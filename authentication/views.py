# views.py - Solo maneja HTTP
import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from core.mixins import SentryErrorHandlerMixin
from .serializers import PasswordResetRequestSerializer, SetNewPasswordSerializer
from .services import PasswordResetService
import sentry_sdk
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from google.oauth2 import id_token
from google.auth.transport import requests
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from decouple import config
from rest_framework.decorators import api_view, permission_classes
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

User = get_user_model()

class PasswordResetRequestView(SentryErrorHandlerMixin, generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    sentry_operation_name = "password_reset_request"
    
    def post(self, request):
        return self.handle_with_sentry(
            operation=self._request_password_reset,
            request=request,
            tags={
                'app': __name__,
                'authenticated': request.user.is_authenticated,
                'component': 'PasswordResetRequestView._request_password_reset',                
            },
            success_message={
                'detail': 'Si el usuario existe, se enviará un correo con instrucciones.'
            },
            success_status=status.HTTP_200_OK
        )
                
    def _request_password_reset(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        self.logger.info(f'intento de restablecimiento de contraseña por: {email}')
        PasswordResetService.request_reset(email, request)
        return

class PasswordResetConfirmView(SentryErrorHandlerMixin, generics.GenericAPIView):
    permission_classes = [AllowAny] 
    serializer_class = SetNewPasswordSerializer
    sentry_operation_name = "password_reset_confirm"
    
    def post(self, request):
        return self.handle_with_sentry(
            operation=self._confirm_reset_password,
            request=request,
            tags={
                'app': __name__,
                'authenticated': request.user.is_authenticated,
                'component': 'PasswordResetConfirmView._confirm_reset_password',                
            },
            success_message={
                'detail': 'Contraseña restablecida con éxito.'
            },
            success_status=status.HTTP_200_OK
        )
    
    def _confirm_reset_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = PasswordResetService.confirm_reset(
            uidb64=serializer.validated_data['uidb64'],
            token=serializer.validated_data['token'],
            new_password=serializer.validated_data['new_password']
        )
        
        self.logger.info(f'Contraseña restablecida exitosamente, id:{user.id},{user.email} ')
           
class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = 'http://localhost:8000/accounts/google/login/callback/'

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            user = self.user
            refresh = RefreshToken.for_user(user)
            
            response.data = {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        
        return response
    
def trigger_error(request):
    division_by_zero = 1 / 0