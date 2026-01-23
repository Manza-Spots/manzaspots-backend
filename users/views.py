
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes,authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth.models import User
from core.mixins import OwnerCheckMixin, SentryErrorHandlerMixin, ViewSetSentryMixin
from core.permission import IsOwnerOrReadOnly
from manza_spots.throttling import RegisterThrottle
from spots_routes.utils import RESEND_CONFIRMATION_EMAIL_REQUEST
from users.docs.users import RESPONSE_ACTIVATE_USER, RESPONSE_DESACTIVATE_USER
from users.models import UserProfile
from .serializers import (UserAdminSerializer, UserCreateSerializer, UserPrivateSerializer, UserProfileSerializer, UserProfileThumbSerializer, UserPublicSerializer, 
                          UserUpdateSerializer)
from core.services.email_service import ConfirmUserEmail
from django.conf import settings
from django.core.mail import send_mail
from users.services import UsersService
from rest_framework import viewsets, permissions, generics
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from rest_framework.mixins import (
    ListModelMixin,
    UpdateModelMixin
)
from rest_framework.generics import UpdateAPIView

_MODULE_PATH = __name__

@extend_schema_view(
    list=extend_schema(
        summary="Listar usuarios",
        tags=["users"],
        description=(
            "Obtiene la lista completa de usuarios del sistema.\n\n"
            "Solo accesible para administradores.\n\n"
            f"**Code:** `{_MODULE_PATH}.UserViewSet_list`"
        ),
        responses={200: UserAdminSerializer(many=True)}
    ),
    retrieve=extend_schema(
        summary="Obtener usuario",
        tags=["users"],
        description=(
            "Obtiene la información detallada de un usuario por su ID.\n\n"
            f"**Code:** `{_MODULE_PATH}.UserViewSet_retrieve`"
        ),
        responses={200: UserAdminSerializer}
    ),
    create=extend_schema(
        summary="Crear usuario",
        tags=["users"],
        description=(
            "Crea un nuevo usuario en estado inactivo.\n\n"
            "Se envía un correo de verificación para activar la cuenta.\n\n"
            "Accesible para cualquier usuario (registro público).\n\n"
            f"**Code:** `{_MODULE_PATH}.UserViewSet_create`"
        ),
        request=UserCreateSerializer,
        responses={
            201: OpenApiResponse(description="Usuario creado. Revisa tu correo para verificar la cuenta."),
            400: OpenApiResponse(description="Datos inválidos")
        }
    ),
    update=extend_schema(
        summary="Actualizar usuario completo",
        tags=["users"],
        description=(
            "Actualiza todos los campos de un usuario.\n\n"
            "Solo accesible para administradores.\n\n"
            f"**Code:** `{_MODULE_PATH}.UserViewSet_update`"
        ),
        request=UserUpdateSerializer,
        responses={200: UserAdminSerializer}
    ),
    partial_update=extend_schema(
        summary="Actualizar usuario parcialmente",
        tags=["users"],
        description=(
            "Actualiza uno o más campos de un usuario.\n\n"
            "Solo accesible para administradores.\n\n"
            f"**Code:** `{_MODULE_PATH}.UserViewSet_partial_update`"
        ),
        request=UserUpdateSerializer,
        responses={200: UserAdminSerializer}
    ),
    destroy=extend_schema(
        summary="Eliminar usuario",
        tags=["users"],
        description=(
            "Desactiva un usuario del sistema (soft delete).\n\n"
            "El usuario no se elimina físicamente.\n\n"
            "Solo accesible para administradores.\n\n"
            f"**Code:** `{_MODULE_PATH}.UserViewSet_destroy`"
        ),
        responses={204: OpenApiResponse(description="Usuario desactivado")}
    )
)
class UserViewSet(OwnerCheckMixin,ViewSetSentryMixin ,viewsets.ModelViewSet):
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        
        if self.action == 'create':
            return UserCreateSerializer
        
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        
        elif self.action == 'retrieve':
            if self.request.user.is_staff:
                return UserAdminSerializer
            
            elif self.is_own_profile():
                return UserPrivateSerializer
            
            else:
                return UserPublicSerializer
        
        elif self.action == 'list':
            if self.request.user.is_staff:
                return UserAdminSerializer
            else:
                return UserPublicSerializer
        
        return UserAdminSerializer
    
    def get_permissions(self):
        """Define permisos según la acción"""
        
        # Registrarse - cualquiera puede
        if self.action == 'create':
            permission_classes = [AllowAny]
        
        elif self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]  
        
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
        
        elif self.action == 'destroy':
            permission_classes = [IsAdminUser]
        
        elif self.action == 'resend_verification_email': 
            permission_classes = [AllowAny]
        
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
   
    def get_throttles(self):
        if self.action in ['create', 'resend_verification_email']:
            return [RegisterThrottle()]
        return super().get_throttles()
    
    def perform_destroy(self, instance):
        """Desactiva el usuario en lugar de eliminarlo"""
        instance.is_active = False
        instance.save()
    
    def create(self, request, *args, **kwargs):
        return self.handle_with_sentry(
            operation=self._create,
            request=request,
            tags={
                'app': __name__,
                'authenticated': request.user.is_authenticated,
                'component': 'UserViewSet._create',
            },
            success_message={
                'detail': 'Usuario creado. Revisa tu correo para verificar la cuenta.'
            },
            success_status=status.HTTP_201_CREATED
        )
    
    def _create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(is_active=False)  

        token = UsersService.generate_email_token(user)

        verify_url = f"/users/verify-email?token={token}"
        confirm_url = request.build_absolute_uri(verify_url)
                        
        ConfirmUserEmail.send_email(
            to_email=user.email, 
            confirm_url=confirm_url, 
            nombre=user.username
        )
        self.logger.info(f'Se a creado el usuario inactivo {user.username}, y enviado el correo de confirmacion a {user.email}')

        headers = self.get_success_headers(serializer.data)
        return Response(
            {"detail": "Usuario creado. Revisa tu correo para verificar la cuenta."},
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    @extend_schema(
        summary="Activar usuario",
        tags=["users"],
        description=(
            "Activa un usuario del sistema.\n\n"
            "Solo accesible para administradores.\n\n"
            f"**Code:** `{_MODULE_PATH}.UserViewSet_activate`"
        ),
        request=None,   
        responses=RESPONSE_ACTIVATE_USER
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def activate(self, request, pk=None):
        """
        Activa un usuario
        POST /users/{id}/activate/
        """
        user = self.get_object()
        user.is_active = True
        user.save()
        self.logger.info(f'Se activo la cuenta del usuario {user.username}')
        return Response(
            {"detail": f"Usuario {user.username} activado."},
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        summary="Desactivar usuario",
        tags=["users"],
        description=(
            "Desactiva un usuario del sistema.\n\n"
            "Solo accesible para administradores.\n\n"
            f"**Code:** `{_MODULE_PATH}.UserViewSet_deactivate`"
        ),
        responses=RESPONSE_DESACTIVATE_USER,
        request=None
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def deactivate(self, request, pk=None):
        """
        Desactiva un usuario
        POST /users/{id}/deactivate/
        """
        user = self.get_object()
        user.is_active = False
        user.save()
        self.logger.info(f'Se activo la cuenta del usuario {user.username}')
        return Response(
            {"detail": f"Usuario {user.username} desactivado."},
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        summary="Usuarios activos",
        tags=["users"],
        description=(
            "Obtiene la lista de usuarios activos.\n\n"
            "Solo accesible para administradores.\n\n"
            f"**Code:** `{_MODULE_PATH}.UserViewSet_active`"
        ),
        responses={200: UserAdminSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def active(self, request):
        """
        Lista solo usuarios activos
        GET /users/active/
        """
        active_users = self.queryset.filter(is_active=True)
        serializer = self.get_serializer(active_users, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Usuarios inactivos",
        tags=["users"],
        description=(
            "Obtiene la lista de usuarios inactivos.\n\n"
            "Solo accesible para administradores.\n\n"
            f"**Code:** `{_MODULE_PATH}.UserViewSet_inactive`"
        ),
        responses={200: UserAdminSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def inactive(self, request):
        """
        Lista solo usuarios inactivos
        GET /users/inactive/
        """
        inactive_users = self.queryset.filter(is_active=False)
        serializer = self.get_serializer(inactive_users, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Usuario actual",
        tags=["users"],
        description=(
            "Obtiene la información del usuario autenticado actualmente.\n\n"
            "Accesible para cualquier usuario autenticado.\n\n"
            f"**Code:** `{_MODULE_PATH}.UserViewSet_me`"
        ),
        responses={
            200: UserAdminSerializer,
            401: OpenApiResponse(description="No autenticado")
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def me(self, request):
        """
        retorna los datos del usuario actual (sesion iniciada)
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data) 

    @extend_schema(
        summary="Reenviar correo de verificacion",
        tags=["users"],
        description=(
            "Se envia al usuario un la opcion de verificar su cuenta (activarla) por correo.\n\n"
            "Pensado para ser utilizado en casos donde al usuario no le llego este correo al crear su cuenta\n\n"
            f"**Code:** `{_MODULE_PATH}.UserViewSet_me`"
        ),
        responses={
            201: OpenApiResponse(description="Usuario creado. Revisa tu correo para verificar la cuenta."),
            400: OpenApiResponse(description="Datos inválidos")
        },
        request=RESEND_CONFIRMATION_EMAIL_REQUEST,
        
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def resend_verification_email(self, request):
            email = request.data.get('email')

            if not email:
                return Response(
                    {"error": "Email is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"message": "si el correo existe, te llegara una notificacion para verificar tu cuenta"}, 
                    status=status.HTTP_200_OK
                )
            
            if user.is_active == True:  
                return Response(
                    {"error": "La cuenta ya fue verificada"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = UsersService.generate_email_token(user)
            
            verify_url = f"/users/verify-email?token={token}"
            confirm_url = request.build_absolute_uri(verify_url)
            
            ConfirmUserEmail.send_email(
                to_email=user.email, 
                confirm_url=confirm_url, 
                nombre=user.username
            )
            
            self.logger.info(f'Re-enviado email de confirmación a {user.username} - {user.email}')
            
            return Response(
                {"message": "Correo de verifiacion enviado"}, 
                status=status.HTTP_200_OK
            )
    
@extend_schema(
    summary="Verificar Cuenta",
    tags=["users"],
    description=(
        "Este endpoint se utiliza despues de crear un usuario, \n\n"
        "Confirma la cuenta de un usuario mediante un token enviado por correo electrónico.\n\n"
        "El token se envía como query parameter y se valida para activar la cuenta.\n\n"
        "Este endpoint no requiere autenticación.\n\n"
        f"**Code:** `{_MODULE_PATH}.confirm_user`"
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
    responses={
        200: OpenApiResponse(description="Usuario verificado con éxito"),
        400: OpenApiResponse(description="Token no proporcionado"),
        401: OpenApiResponse(description="Token inválido o expirado"),
        404: OpenApiResponse(description="Usuario no encontrado"),
        409: OpenApiResponse(description="El correo ya fue verificado")
    }
)        
@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def confirm_user(request):
    handler = SentryErrorHandlerMixin()  
    handler._logger = logging.getLogger(__name__)
    
    def operation(_):
        token = request.query_params.get('token')
        
        if not token:
            return Response({'detail': 'Token no proporcionado.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = UsersService.verify_email_token(token)
        if not user_id:
            return Response({'detail': 'Token inválido o expirado.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
        if user.is_active:
            return Response({'detail': 'El usuario ya fue verificado.'}, status=status.HTTP_409_CONFLICT)
                
        user.is_active = True
        user.save()
        handler.logger.info(f'Se confirmo el correo de {user.username}, ahora su cuenta esta activa')
        return Response({'detail': 'Usuario verificado con éxito.'}, status=status.HTTP_200_OK)
    
    return handler.handle_with_sentry(
        operation=operation,
        request=request,
        tags={'endpoint': 'confirm_user'},
        success_message={'detail': 'Correo verificado con éxito'}
    )



@extend_schema(
    summary="Actualizar thumbnail del perfil",
    tags=["users"],
    description=(
        "Actualiza únicamente la imagen de perfil (thumbnail) del usuario autenticado.\n\n"
        "Este endpoint **no permite** modificar ningún otro campo del perfil.\n\n"
        "No requiere enviar ID, el perfil se obtiene automáticamente desde la sesión activa.\n\n"
        f"**Code:** `{_MODULE_PATH}.UpdateProfileThumbView`"
    ),
    request=UserProfileThumbSerializer,
    responses={200: UserProfileThumbSerializer}
)
class UpdateProfileThumbView(UpdateAPIView):
    serializer_class = UserProfileThumbSerializer
    permission_classes = [IsAuthenticated]
    queryset = UserProfile.objects.all()
    
    def get_object(self):
        return self.request.user.profile
