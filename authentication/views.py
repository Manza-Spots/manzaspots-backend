# views.py - Solo maneja HTTP
import logging
import re
import unicodedata
from urllib import request
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from authentication.docs.auth import CONFIRM_NEW_PASSWORD_RESPONSE, FACEBOOK_LOGIN_REQUEST, GOOGLE_LOGIN_REQUEST, LOGIN_RESPONSE, REQUEST_NEW_PASSWORD_RESPONSE
from core.mixins import SentryErrorHandlerMixin
from manza_spots.throttling import LoginThrottle, SensitiveOperationThrottle
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
    
    def get_throttles(self):
        if self.action == 'create':
            return [SensitiveOperationThrottle()]
        return super().get_throttles()
    
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
                "Actualiza la contraseña del usuario utilizando el token de restablecimiento y el identificador"
                "de usuario previamente enviados en la solicitud de recuperación de contraseña. \n\n  "
                f"**Code:** `{_MODULE_PATH}.PasswordResetConfirmView`"
            ),
            responses=CONFIRM_NEW_PASSWORD_RESPONSE,
       )
    
    def get_throttles(self):
        if self.action == 'create':
            return [SensitiveOperationThrottle()]
        return super().get_throttles()
    
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

    def get_throttles(self):
        if self.request.method == 'POST':
            return [SensitiveOperationThrottle()]
        return super().get_throttles()
    
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
    
class CustomFacebookOAuth2Adapter(FacebookOAuth2Adapter):
    """Adaptador profesional con generación de username único garantizado"""
    
    def complete_login(self, request, app, token, **kwargs):
        login = super().complete_login(request, app, token, **kwargs)
        
        extra_data = login.account.extra_data
        User = get_user_model()
        
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
@extend_schema(
    summary="Autenticación con Facebook",
    tags=["auth"],
    description=(
        "Autentica o registra usuarios mediante Facebook como proveedor externo, validando un token emitido por Facebook y retornando "
        "los tokens de acceso de la aplicación\n\n"
        "En caso de no contar con el SDK de Facebook en el frontend para realizar pruebas, acceder a Facebook Developer -> Herramientas -> Explorador de la API Graph.\n\n"        
        f"**Code:** `{_MODULE_PATH}.FacebookLogin`"
    ),
    request=FACEBOOK_LOGIN_REQUEST,
    responses=LOGIN_RESPONSE,
)
class FacebookLogin(SocialLoginView):
    """Login de Facebook con username basado en nombre"""
    adapter_class = CustomFacebookOAuth2Adapter
    client_class = OAuth2Client
    
    def post(self, request, *args, **kwargs):
        print("=" * 60)
        print("🔵 FACEBOOK LOGIN - DEBUG")
        print(f"Token: {request.data.get('access_token', 'NO TOKEN')[:40]}...")
        
        try:
            response = super().post(request, *args, **kwargs)
            
            print(f"✅ Response status: {response.status_code}")
            
            if response.status_code == 200:
                user = self.user if hasattr(self, 'user') else request.user
                
                print(f"👤 Usuario autenticado:")
                print(f"   - Username: {user.username}")
                print(f"   - Email: {user.email}")
                print(f"   - Nombre: {user.first_name} {user.last_name}")
                
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }, status=status.HTTP_200_OK)
            
            return response
            
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

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
    throttle_classes = [LoginThrottle]
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