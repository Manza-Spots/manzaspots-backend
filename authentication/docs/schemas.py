from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from authentication.docs.request import GOOGLE_LOGIN_REQUEST, RESEND_CONFIRMATION_EMAIL_REQUEST
from authentication.docs.response import LOGIN_RESPONSE
from authentication.serializers import UserCreateSerializer
from core.responses.messages import AuthMessages, UserMessages
from core.responses.schemas import UserResponses
_MODULE_PATH_JWT = 'auth.views.jwt_views'
_MODULE_PATH_SOCIAL = 'auth.views.oauth_views'
_MODULE_PATH_PASSWORD = 'authentication.views.password_views'
_MODULE_PATH_USER = 'authentication.views.user_views'
#========================================== JWT VIEWS ================================================

LOGIN_SCHEMA = extend_schema(
    tags=['auth'],
    summary='Iniciar Sesión',
    description=(
        'Autenticación con **username o email** + contraseña.\n\n'
        'Retorna access y refresh tokens.\n\n'
        f'**Code:** `{_MODULE_PATH_JWT}.LoginView`'
    ),
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {
                    'type': 'string',
                    'example': 'usuario@example.com',
                    'description': 'Username o email del usuario'
                },
                'email': {
                    'type': 'string',
                    'example': 'usuario@example.com',
                    'description': 'Email del usuario (alternativa a username)'
                },
                'password': {'type': 'string', 'example': 'password123'}
            },
            'required': ['password']
        }
    },
    responses=LOGIN_RESPONSE
)

TOKEN_REFRESH = extend_schema(
    summary="Renovar access token",
    description=(
        "Genera un nuevo **access token** usando un **refresh token válido**.\n\n"
        f"**Code:** `{_MODULE_PATH_JWT}.TokenRefreshView`"
    ),
    tags=["auth"]
)

TOKEN_VERIFY = extend_schema(
    summary="Verificar token JWT",
    tags=["auth"],
    description=f"Verifica si un JWT es válido.\n\n**Code:** `{_MODULE_PATH_JWT}.TokenVerifyView`"
)

LOGOUT = extend_schema(
    tags=['auth'],
    summary='Cerrar sesión',
    description=(
        'Invalida el refresh token agregándolo a la blacklist.\n\n'
        f"**Code:** `{_MODULE_PATH_JWT}.LogoutView`"
    ),
    responses={
        200: OpenApiResponse(description='Logout exitoso'),
        400: OpenApiResponse(description='Token inválido')
    }
)

#========================================== SOCIAL VIEWS ================================================
GOOGLE = extend_schema(
    summary="Autenticación con Google",
    tags=["auth"],
    description=(
        "Autentica o registra usuarios mediante Google.\n\n"
        "El email se verifica automáticamente.\n\n"
        f"**Code:** `{_MODULE_PATH_SOCIAL}.GoogleLoginView`"
    ),

    request=GOOGLE_LOGIN_REQUEST,
    responses=LOGIN_RESPONSE
)

FACEBOOK = extend_schema(
    summary="Autenticación con Facebook",
    tags=["auth"],
    description=(
        "Autentica o registra usuarios mediante Facebook.\n\n"
        "El email se verifica automáticamente.\n\n"
        f"**Code:** `{_MODULE_PATH_SOCIAL}.FacebookLoginView`"
    ),

    request=GOOGLE_LOGIN_REQUEST,
    responses=LOGIN_RESPONSE,
)
#========================================== PASSWORD VIEWS ================================================

PASSWORD_RESET_REQUEST = extend_schema(
    summary="Solicitar restablecimiento de contraseña",
    tags=["auth"],
    description=(
        "Solicita el restablecimiento de contraseña.\n\n"
        "Por seguridad, no revela si el email existe.\n\n"
        f"**Code:** `{_MODULE_PATH_PASSWORD}.PasswordResetRequestView`"
    ),
    responses={
        200: {'description': UserMessages.EMAIL_SENT_IF_EXISTS}
    }
)

PASSWORD_RESET_CONFIRM = extend_schema(
    summary="Confirmar nueva contraseña",
    tags=["auth"],
    description=(
        "Actualiza la contraseña usando el token de restablecimiento.\n\n"
        f"**Code:** `{_MODULE_PATH_PASSWORD}.PasswordResetConfirmView`"
    ),
    responses={
        200: {'description': AuthMessages.CONFIRM_NEW_PASSWORD},
        400: {'description': UserMessages.TOKEN_INVALID}
    }
)

#========================================== USER VIEWS ================================================
REGISTRATION = extend_schema(
    summary="Registrarse/Crear usuario",
    tags=["auth"],
    description=(
        "Crea un nuevo usuario en estado inactivo.\n\n"
        "Se envía un correo de verificación para activar la cuenta.\n\n"
        "Accesible para cualquier usuario (registro público).\n\n"
        f"**Code:** `{_MODULE_PATH_USER}.UserViewSet_create`"
    ),
    request=UserCreateSerializer,
    responses={
        201: OpenApiResponse(description=UserMessages.USER_CREATED),
    }
)

VERIFY_USER = extend_schema(
    summary="Verificar Cuenta",
    tags=["auth"],
    description=(
        "Este endpoint se utiliza despues de crear un usuario, \n\n"
        "Confirma la cuenta de un usuario mediante un token enviado por correo electrónico.\n\n"
        "El token se envía como query parameter y se valida para activar la cuenta.\n\n"
        "Este endpoint no requiere autenticación.\n\n"
        f"**Code:** `{_MODULE_PATH_USER}.confirm_user`"
    ),
    parameters=[
        OpenApiParameter(
            name="token",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Token de verificación enviado por correo",
            required=True
        )
    ],
    responses=UserResponses.VERIFIED_200
)   

RESEND_TOKEN = extend_schema(
    summary="Reenviar correo de verificacion",
    tags=["auth"],
    description=(
        "Se envia al usuario un la opcion de verificar su cuenta (activarla) por correo.\n\n"
        "Pensado para ser utilizado en casos donde al usuario no le llego este correo al crear su cuenta\n\n"
        f"**Code:** `{_MODULE_PATH_USER}.UserViewSet_me`"
    ),
    responses={
        201: OpenApiResponse(description=UserMessages.USER_CREATED),
    },
    request=RESEND_CONFIRMATION_EMAIL_REQUEST,
    
)

VERIFY_EMAIL = extend_schema(
    summary="Verificar Cuenta/EMAIL",
    tags=["users"],
    description=(
        "Este endpoint se utiliza como metodo de seguridad para confirmas tokens provenientes de un correo\n\n"
        "Como el caso de confirmar el correo de un usuario despues de crearlo o modificar su correo \n\n"
        "Confirma la cuenta de un usuario mediante un token enviado por correo electrónico.\n\n"
        "El token se envía como query parameter y se valida para activar la cuenta.\n\n"
        "Este endpoint no requiere autenticación.\n\n"
        f"**Code:** `{_MODULE_PATH_USER}.VerifyEmailAPIView`"
    ),
    parameters=[
        OpenApiParameter(
            name="token",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Token de verificación enviado por correo",
            required=True
        )
    ],
    responses=UserResponses.VERIFIED_200
)  