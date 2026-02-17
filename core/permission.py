from django.contrib.auth import get_user_model

User = get_user_model()
from rest_framework import viewsets, status, generics,permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso que permite lectura a todos, pero solo escritura al dueño.
    Funciona con modelos User directamente o modelos con atributo 'user'.
    """
    
    def has_object_permission(self, request, view, obj):
        # Lectura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Determinar el dueño según el tipo de objeto
        if isinstance(obj, User):
            # Si el objeto ES un User
            owner = obj
        elif hasattr(obj, 'user'):
            # Si el objeto tiene un atributo 'user'
            owner = obj.user
        elif request.user.is_staff or request.user.is_superuser:
            return True
        else:
            # No se puede determinar el dueño
            return False

        return owner == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso personalizado: solo el propietario o admin puede editar
    """
    def has_object_permission(self, request, view, obj):
        # Los admins pueden todo
        if request.user.is_staff:
            return True
        # El propietario puede editar su propio spot
        return obj.user == request.user