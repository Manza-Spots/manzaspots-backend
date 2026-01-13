# views.py - Solo maneja HTTP
import logging
from urllib import request
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from authentication.docs.auth import CONFIRM_NEW_PASSWORD_RESPONSE, GOOGLE_LOGIN_REQUEST, LOGIN_RESPONSE, REQUEST_NEW_PASSWORD_RESPONSE
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
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework_simplejwt.views import (
    TokenRefreshView,TokenVerifyView, TokenObtainPairView,TokenBlacklistView
)
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter

User = get_user_model()
_MODULE_PATH = __name__

class PasswordResetRequestView(SentryErrorHandlerMixin, generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    sentry_operation_name = "password_reset_request"
    
    @extend_schema(
        summary="Solicitar nueva contraseña",
        tags=["auth"],
        description=(
            "Solicita el restablecimiento de contraseña a partir del correo proporcionado. \n\n "
            "Si el correo no existe, no se revela esta información al usuario.  \n\n"
            "Si existe, se envía un token de restablecimiento al correo registrado.\n\n"
            f"**Code:** `{_MODULE_PATH}.PasswordResetRequestView`"
        ),
        responses=REQUEST_NEW_PASSWORD_RESPONSE
    )
    
    def post(self, request):
        return self.handle_with_sentry(
            operation=self._request_password_reset,
            request=request,
            tags={
                'app': __name__,
                'authenticated': request.user.is_authenticated,
                'component': f'{_MODULE_PATH}._request_password_reset',                
            },
            success_message = { "detail": "Si el usuario existe, se enviará un correo con instrucciones."},
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
    
    @extend_schema(
            summary="Confirmas Nueva Contraseña",
            tags=["auth"],
            description=(
                "Actualiza la contraseña del usuario utilizando el token de restablecimiento y el identificador \n\n"
                "de usuario previamente enviados en la solicitud de recuperación de contraseña. \n\n  "
                f"**Code:** `{_MODULE_PATH}.PasswordResetConfirmView`"
            ),
            responses=CONFIRM_NEW_PASSWORD_RESPONSE,
       )
    
    
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
        
@extend_schema(
    summary="Autenticacion con Google",
    tags=["auth"],
    description=(
        "Autentica o registra usuarios mediante Google como proveedor externo, validando un token emitido por Google y retornando "
        "los tokens de acceso de la aplicación\n\n"
        f"**Code:** `{_MODULE_PATH}.GoogleLogin`"
    ),
    request=GOOGLE_LOGIN_REQUEST,
    responses=LOGIN_RESPONSE,
)
class GoogleLogin(SentryErrorHandlerMixin, SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = 'http://localhost:8000/accounts/google/login/callback/'
    sentry_operation_name = "google_authentication"

    def post(self, request, *args, **kwargs):
        return self.handle_with_sentry(
            operation=self._google_login,
            request=request,
            tags={
                'app': __name__,
                'authenticated': request.user.is_authenticated,
                'component': 'GoogleLogin._google_login',
            },
            success_message={
                'detail': 'Autenticación con Google exitosa.'
            },
            success_status=status.HTTP_200_OK
        )
    
    def _google_login(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            user = self.user
            refresh = RefreshToken.for_user(user)
            self.logger.info(f'Se a creado un nuevo usuario ({user.username}, a partir de google authentication)')
            response.data = {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        
        return response
    
    
#=============== DOCUMENTACION PARA TOKENS NADA MAS =====================

@extend_schema(
    summary="Renovar access token",
    description=(
        "Genera un nuevo **access token** usando un **refresh token válido**.\n\n"
        "Solo funciona si el refresh token sigue siendo válido\n\n"
        "Tiempo antes de caducar: 60 min\n\n"
        f"**Code:** `{_MODULE_PATH}.DocumentedTokenRefreshView`"
    ),
    tags=["auth"],
    examples=[
        OpenApiExample(
            "Request válido",
            value={
                "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
            },
            request_only=True,
        ),
        OpenApiExample(
            "Respuesta exitosa",
            value={
                "refresh":"nuevo_refresh_token",
                "access": "nuevo_access_token"
            },
            response_only=True,
        ),
    ],
)
class DocumentedTokenRefreshView(TokenRefreshView):
    pass

@extend_schema(
    summary="Verificar token JWT",
    tags=["auth"],
    description=
    "Verifica si un **JWT** es válido.\n\n"
    "Tiempo antes de caducar: 7 dias\n\n"
    f"**Code:** `{_MODULE_PATH}.DocumentedTokenRefreshView`"
    ,
    examples=[
        OpenApiExample(
            "Request",
            value={
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
            },
            request_only=True,
        ),
    ],
)
class DocumentedTokenVerifyView(TokenVerifyView):
    pass

@extend_schema(
        tags=['auth'],
        summary='Iniciar Sesion',
        description='Endpoint para autenticacin. \n\n Retorna access y refresh tokens. \n\n'
                    f"**Code:** `{_MODULE_PATH}.DocumentedTokenObtainPairView`",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string', 'example': 'usuario@example.com'},
                    'password': {'type': 'string', 'example': 'password123'}
                },
                'required': ['username', 'password']
            }
        },
        responses = LOGIN_RESPONSE
    )
class DocumentedTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
@extend_schema(
        tags=['auth'],
        summary='Cerrar sesión',
        description='Invalida el refresh token agregándolo a la blacklist. \n\n El access token seguirá siendo válido hasta que expire. \n\n'
                    f"**Code:** `{_MODULE_PATH}.DocumentedTokenBlacklistView`",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh': {
                        'type': 'string',
                        'description': 'Refresh token a invalidar',
                        'example': 'eyJ0eXAiOiJKV1QiLCJhbGc...'
                    }
                },
                'required': ['refresh']
            }
        },
        responses={
            200: OpenApiResponse(
                description='Logout exitoso',
                examples=[
                    OpenApiExample(
                        'Respuesta exitosa',
                        value={'detail': 'Sesión cerrada exitosamente'}
                    )
                ]
            ),
            400: OpenApiResponse(description='Token inválido o ya invalidado'),
            401: OpenApiResponse(description='No autenticado')
        }
    )
class DocumentedTokenBlacklistView(TokenBlacklistView):    
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)