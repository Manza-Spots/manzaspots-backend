from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser,IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from spots_routes.models import Spot, SpotCaption, SpotStatusReview, UserFavoriteSpot
from spots_routes.serializer import SpotCaptionCreateSerializer, SpotCaptionSerializer, SpotSerializer, UserFavoriteSpotSerializer
from django.utils import timezone
from spots_routes import models

class SpotViewSet(viewsets.ModelViewSet):
    serializer_class = SpotSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        # Excepción: acción 'list' pública
        if self.action == 'list':
            return []  # sin permisos → acceso libre

        # Todo lo demás sigue requiriendo autenticación
        return [permission() for permission in self.permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Spot.objects.filter(deleted_at__isnull=True)
                
        if self.action == 'list':
            if user.is_authenticated:
                if user.is_staff:
                    status_param = self.request.query_params.get('status')
                    if status_param:
                        queryset = queryset.filter(status__key=status_param)
            else:
                # Usuarios normales: solo spots activos y aceptados
                queryset = queryset.filter(
                    is_active=True,
                    status__key='APPROVED'
                )
            
            # Filtro por nombre
            name = self.request.query_params.get('name')
            if name:
                queryset = queryset.filter(name__icontains=name)
        
        return queryset
    
    def perform_create(self, serializer):
        """Asignar usuario y estado inicial al crear"""
        #user metodo establecido en models
        serializer.save(
            user=self.request.user,
            status_id=models.get_default_pending()
        )
    
    def update(self, request, *args, **kwargs):
        """Permitir edición solo al propietario o admin"""
        spot = self.get_object()
        
        # Validar permisos
        if not request.user.is_staff and spot.user != request.user:
            return Response(
                {'error': 'No tienes permiso para editar este spot'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Mismo control para PATCH"""
        return self.update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def authorize(self, request, pk=None):
        """Autorizar un spot"""
        spot = self.get_object()
        # id_status = models.get_approved()
        spot.status_id = models.get_approved()  
        spot.is_active = True
        spot.reviewed_user = request.user
        spot.reviewed_at = timezone.now()
        spot.save()
        
        serializer = self.get_serializer(spot)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def deny(self, request, pk=None):
        """Denegar un spot"""
        spot = self.get_object()
        reason = request.data.get('reason')
        
        if not reason:
            return Response(
                {'error': 'Se requiere una razón para rechazar'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        spot.status_id = models.get_rejected()
        spot.reject_reason = reason
        spot.is_active = False
        spot.reviewed_user = request.user
        spot.reviewed_at = timezone.now()
        spot.save()
        
        serializer = self.get_serializer(spot)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_spots(self, request):
        """Spots del usuario actual"""
        queryset = Spot.objects.filter(
            user=request.user,
            deleted_at__isnull=True
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_to_favorites(self, request, pk=None):
        """Agregar spot a favoritos"""
        spot = self.get_object()
        
        favorite, created = UserFavoriteSpot.objects.get_or_create(
            user=request.user,
            spot=spot,
            defaults={'is_active': True}
        )
        
        if not created:
            # Si ya existe, activarlo
            if not favorite.is_active:
                favorite.is_active = True
                favorite.save()
                return Response({'status': 'reactivated'})
            return Response(
                {'status': 'already_favorited'},
                status=status.HTTP_200_OK
            )
        
        return Response({'status': 'added'}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def remove_from_favorites(self, request, pk=None):
        """Remover de favoritos (soft delete)"""
        spot = self.get_object()
        
        try:
            favorite = UserFavoriteSpot.objects.get(
                user=request.user,
                spot=spot
            )
            favorite.is_active = False
            favorite.save()
            return Response({'status': 'removed'})
        except UserFavoriteSpot.DoesNotExist:
            return Response(
                {'error': 'Este spot no está en tus favoritos'},
                status=status.HTTP_404_NOT_FOUND
            )


class UserFavoriteSpotsView(generics.ListAPIView):
    """Vista para listar favoritos del usuario actual"""
    serializer_class = UserFavoriteSpotSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserFavoriteSpot.objects.filter(
            user=self.request.user,
            is_active=True,
            spot__deleted_at__isnull=True
        ).select_related('spot')
        
        
class SpotCaptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar los captions de spots
    
    list: Ver todos los captions (opcional, o filtrados por spot)
    create: Crear un nuevo caption
    retrieve: Ver un caption específico
    update/destroy: Solo el dueño o admin puede editar/eliminar
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SpotCaptionCreateSerializer
        return SpotCaptionSerializer
    
    def get_queryset(self):
        queryset = SpotCaption.objects.select_related('user', 'spot')
        
        # Filtrar por spot si se pasa como parámetro
        spot_id = self.request.query_params.get('spot')
        if spot_id:
            queryset = queryset.filter(spot_id=spot_id)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        # Asignar automáticamente el usuario autenticado
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        # Solo el dueño o admin puede actualizar
        if self.request.user != serializer.instance.user and not self.request.user.is_staff:
            raise PermissionDenied("No tienes permiso para editar este caption")
        serializer.save()
    
    def perform_destroy(self, instance):
        # Solo el dueño o admin puede eliminar
        if self.request.user != instance.user and not self.request.user.is_staff:
            raise PermissionDenied("No tienes permiso para eliminar este caption")
        instance.delete()