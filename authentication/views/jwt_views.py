"""
Vistas para autenticación JWT tradicional (username/email + password).
"""
from rest_framework.response import Response 
from rest_framework_simplejwt.views import (
    TokenRefreshView, TokenVerifyView, 
    TokenObtainPairView, TokenBlacklistView
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from django.contrib.auth import authenticate, get_user_model
from authentication.base import BaseAuthenticationView, BaseJWTView
from authentication.docs.schemas import LOGIN_SCHEMA, LOGOUT, TOKEN_REFRESH, TOKEN_VERIFY
from authentication.serializers import CustomTokenObtainPairSerializer
from manza_spots.throttling import LoginThrottle
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from core.responses.messages import AuthMessages
from authentication.base import BaseAuthenticationView

User = get_user_model()
_MODULE_PATH = 'auth.views.jwt_views'


@LOGIN_SCHEMA
class LoginView(BaseJWTView, GenericAPIView):
    """Vista de login personalizada con soporte para username o email"""
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]
    sentry_operation_name = "jwt_login"

    def post(self, request, *args, **kwargs):
        return self.handle_with_sentry(
            operation=self._jwt_login,
            request=request,
            tags={
                'app': 'authentication',
                'component': 'LoginView',
                'provider': 'jwt'
            },
            success_status=status.HTTP_200_OK
        )

    def _jwt_login(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        # Validar password
        if not password:
            return Response(
                AuthMessages.PASSWORDL_REQUIRED,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar username o email
        if not username and not email:
            return Response(
                AuthMessages.EMAIL_USERNAMEL_REQUIRED,
                status=status.HTTP_400_BAD_REQUEST
            )

        user = None

        # Autenticación por email
        if email:
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(
                    request=request,
                    username=user_obj.username,
                    password=password
                )
            except User.DoesNotExist:
                pass

        # Autenticación por username
        if not user and username:
            user = authenticate(
                request=request,
                username=username,
                password=password
            )

        # Credenciales inválidas
        if not user:
            self.log_auth_event(
                'jwt_login_failed',
                user=None,
                success=False,
                reason='Credenciales inválidas',
                ip=request.META.get('REMOTE_ADDR')
            )
            return Response(
                AuthMessages.CREDENTIALS_INVALID,
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generar tokens
        response_data = self.generate_token_response(user)

        # Log de éxito
        self.log_auth_event(
            'jwt_login_success',
            user=user,
            method='username_email'
        )

        return Response(response_data, status=status.HTTP_200_OK)


@TOKEN_REFRESH
class TokenRefreshView(TokenRefreshView):
    pass


@TOKEN_VERIFY
class TokenVerifyView(TokenVerifyView):
    pass


@LOGOUT
class LogoutView(TokenBlacklistView):
    pass