
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth.models import User

from users.models import UserProfile
from .serializers import (UserCreateSerializer, UserSerializer, 
                          UserUpdateSerializer)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar usuarios.
    
    Endpoints:
    - GET /users/                 -> Listar usuarios
    - POST /users/                -> Crear usuario
    - Get /users/me               -> Obtener usuario actual
    - GET /users/{id}/            -> Obtener usuario
    - PUT /users/{id}/            -> Actualizar usuario completo
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
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def activate(self, request, pk=None):
        """
        Activa un usuario
        POST /users/{id}/activate/
        """
        user = self.get_object()
        user.is_active = True
        user.save()
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
        

class UserProfileViewSet(viewsets.ModelViewSet):
    """
        Endpoints:
    - GET /users/profiles                 -> Listar perfiles
    - GET /users/{id}/profiles            -> Obtener perfil
    - GET /users/profiles/me              -> Obtener perfil del usuario actual
    - PUT /users/{id}/profiles            -> Actualizar perfil completo
    - PATCH /users/{id}/profiles          -> Actualizar perfil parcial
    """
    queryset = UserProfile.objects.all()