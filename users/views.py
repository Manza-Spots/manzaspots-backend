
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes,authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth.models import User
from core.mixins import SentryErrorHandlerMixin
from users.models import UserProfile
from .serializers import (UserCreateSerializer, UserProfileSerializer, UserSerializer, 
                          UserUpdateSerializer)
from core.services.email_service import ConfirmUserEmail
from django.conf import settings
from django.core.mail import send_mail
from users.services import UsersService
from rest_framework import viewsets, permissions, generics
from rest_framework.exceptions import PermissionDenied

class UserViewSet(SentryErrorHandlerMixin, viewsets.ModelViewSet):
    """
    ViewSet para manejar usuarios.
    
    Endpoints:
    - GET /users/                 -> Listar usuarios *
    - POST /users/                -> Crear usuario 
    - Get /users/me               -> Obtener usuario actual *
    - GET /users/{id}/            -> Obtener usuario *
    - PUT /users/{id}/            -> Actualizar usuario completo *
    - PATCH /users/{id}/          -> Actualizar usuario parcial
    - DELETE /users/{id}/         -> Eliminar usuario
    - POST /users/{id}/activate/  -> Activar usuario
    - POST /users/{id}/deactivate/ -> Desactivar usuario
    """
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer

        return UserSerializer
    
    def get_permissions(self):
        """Define permisos según la acción"""
        if self.action == 'create':
            # Cualquiera puede registrarse
            permission_classes = [AllowAny]
        else:
            # Solo administradores para otras operaciones
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
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
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def active(self, request):
        """
        Lista solo usuarios activos
        GET /users/active/
        """
        active_users = self.queryset.filter(is_active=True)
        serializer = self.get_serializer(active_users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def inactive(self, request):
        """
        Lista solo usuarios inactivos
        GET /users/inactive/
        """
        inactive_users = self.queryset.filter(is_active=False)
        serializer = self.get_serializer(inactive_users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def me(self, request):
        """
        retorna los datos del usuario actual (sesion iniciada)
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data) 
        

@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def verify_email(request):
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
            return Response({'detail': 'El correo ya fue verificado.'}, status=status.HTTP_409_CONFLICT)
                
        user.is_active = True
        user.save()
        handler.logger.info(f'Se confirmo el correo de {user.username}, ahora su cuenta esta activa')
        return Response({'detail': 'Correo verificado con éxito.'}, status=status.HTTP_200_OK)
    
    return handler.handle_with_sentry(
        operation=operation,
        request=request,
        tags={'endpoint': 'verify_email'},
        success_message={'detail': 'Correo verificado con éxito'}
    )

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile
