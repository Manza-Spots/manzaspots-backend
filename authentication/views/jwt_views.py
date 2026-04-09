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
from authentication.serializers import CustomTokenObtainPairSerializer, LoginSerializer
from authentication.services import LoginService, UsersRegisterService
from core.docs.schema_utils import auto_schema
from core.services.email_service import ConfirmUserEmail
from manza_spots.throttling import LoginThrottle
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from core.responses.messages import AuthMessages
from authentication.base import BaseAuthenticationView

from django.contrib.auth import get_user_model
User = get_user_model()

@auto_schema(**LOGIN_SCHEMA)
class LoginView(BaseJWTView, GenericAPIView):
    """Vista de login personalizada con soporte para username o email"""
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]
    serializer_class = LoginSerializer
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
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data     = serializer.validated_data
        username = data.get('username')
        email    = data.get('email')
        password = data.get('password')
        ip       = request.META.get('REMOTE_ADDR')

        user_obj = LoginService.get_user_by_credential(username=username, email=email)

        if LoginService.check_provider_only_account(user_obj):
            return Response(AuthMessages.USE_PROVIDER_OR_SET_PASSWORD, status=status.HTTP_401_UNAUTHORIZED)
        
        inactive = LoginService.check_inactive_user(user_obj, password, ip) if user_obj else None
        if inactive:
            self.log_auth_event('jwt_login_failed', user=None, success=False,
                                reason=inactive['reason'], ip=ip)
            return Response(inactive['response'], status=status.HTTP_401_UNAUTHORIZED)

        user = LoginService.authenticate_user(request, user_obj=user_obj,
                                            username=username, password=password)
        if not user:
            self.log_auth_event('jwt_login_failed', user=None, success=False,
                                reason='Credenciales inválidas', ip=ip)
            return Response(AuthMessages.CREDENTIALS_INVALID, status=status.HTTP_401_UNAUTHORIZED)

        response_data = self.generate_token_response(user)
        self.log_auth_event('jwt_login_success', user=user, method='username_email')
        return Response(response_data, status=status.HTTP_200_OK)

@auto_schema(**TOKEN_REFRESH)
class TokenRefreshView(TokenRefreshView):
    pass


@auto_schema(**TOKEN_VERIFY)
class TokenVerifyView(TokenVerifyView):
    pass


@auto_schema(**LOGOUT)
class LogoutView(TokenBlacklistView):
    pass