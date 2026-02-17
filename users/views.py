import logging
from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
    AllowAny
)
from rest_framework.response import Response
from rest_framework.generics import UpdateAPIView
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse
)

from core.mixins import OwnerCheckMixin, ViewSetSentryMixin
from core.permission import IsOwnerOrReadOnly
from users.docs.users import RESPONSE_DESACTIVATE_USER
from users.models import UserProfile
from core.services.email_service import UpdateUserEmail
from authentication.services import UsersRegisterService

from .serializers import (
    EmailUpdateSerializer,
    UserAdminSerializer,
    UserPrivateSerializer,
    UserPublicSerializer,
    UserUpdateSerializer,
    UserProfileSerializer,
    UserProfileThumbSerializer
)

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
class UserViewSet(
    OwnerCheckMixin,
    ViewSetSentryMixin,
    viewsets.ModelViewSet
):
    """
    ViewSet exclusivo para la gestión de usuarios.

    - No maneja registro
    - No maneja verificación de correo
    - No maneja activación de cuentas
    """
    queryset = User.objects.all()
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer

        if self.action == 'retrieve':
            if self.request.user.is_staff:
                return UserAdminSerializer
            if self.is_own_profile():
                return UserPrivateSerializer
            return UserPublicSerializer

        if self.action == 'list':
            return UserAdminSerializer if self.request.user.is_staff else UserPublicSerializer

        return UserAdminSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]

        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]

        if self.action == 'destroy':
            return [IsAdminUser()]

        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

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
        active_users = self.queryset.filter(is_active=True).order_by('-created_at')
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
        inactive_users = self.queryset.filter(is_active=False).order_by('-created_at')
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
    summary="Actualizar thumbnail del perfil",
    description="Actualiza la imagen thumbnail del perfil del usuario autenticado.",
    tags=["users"],
    request=UserProfileThumbSerializer,
    responses={200: UserProfileThumbSerializer}
)
class UpdateProfileThumbView(UpdateAPIView):
    serializer_class = UserProfileThumbSerializer
    permission_classes = [IsAuthenticated]
    queryset = UserProfile.objects.all()

    def get_object(self):
        return self.request.user.profile


@extend_schema(
    summary="Solicitar cambio de correo",
    description=(
        "Solicita el cambio de correo electrónico del usuario autenticado. "
        "Si el correo no está registrado previamente, se envía un email "
        "con instrucciones para confirmar el cambio."
    ),
    tags=["users"],
    responses={
        200: OpenApiResponse(
            description="Si el correo existe, recibirás instrucciones"
        )
    }
)
class EmailUpdateAPIView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmailUpdateSerializer
    logger = logging.getLogger(__name__)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = request.user
        message = "Si el correo existe, recibirás instrucciones"

        if User.objects.filter(email=email).exists():
            return Response({"message": message}, status=status.HTTP_200_OK)

        confirm_url = UsersRegisterService.get_confirmation_url(
            user=user,
            request=request,
            email=email
        )

        UpdateUserEmail.send_email(
            to_email=email,
            confirm_url=confirm_url,
            nombre=user.username
        )

        self.logger.info(
            f"Solicitud de cambio de correo: {user.username} -> {email}"
        )

        return Response({"message": message}, status=status.HTTP_200_OK)