from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from core.mixins import ViewSetSentryMixin
from spots_routes.models import Spot, SpotCaption, SpotStatusReview, UserFavoriteSpot
from spots_routes.serializer import (
    SpotCaptionCreateSerializer, 
    SpotCaptionSerializer, 
    SpotSerializer, 
    UserFavoriteSpotSerializer
)
from django.utils import timezone
from spots_routes import models
_MODULE_PATH = __name__

@extend_schema_view(
    list=extend_schema(
        summary="Listar spots",
        tags=["spots"],
        description=(
            "Obtiene la lista de spots del sistema.\n\n "
            "Los usuarios no autenticados y autenticados solo verán spots activos y aprobados. \n\n"
            "Los administradores pueden filtrar por estado.\n\n"
            f"**Code:** `{_MODULE_PATH}.SpotViewSet_list`"
        ),
        parameters=[
            OpenApiParameter(
                name='name',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Filtrar spots por nombre (búsqueda parcial)',
                required=False
            ),
            OpenApiParameter(
                name='status',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Filtrar por estado (solo para administradores): PENDING, APPROVED, REJECTED',
                required=False
            )
        ]
    ),
    retrieve=extend_schema(
        summary="Obtener detalle de spot",
        tags=["spots"],
        description="Obtiene la información detallada de un spot específico por su ID. \n\n"
        f"**Code:** `{_MODULE_PATH}.SpotViewSet_retrieve`"
    ),
    create=extend_schema(
        summary="Crear nuevo spot",
        tags=["spots"],
        description=(
            "Crea un nuevo spot. El spot se crea en estado PENDING y será"
            "asignado automáticamente al usuario autenticado. \n\n"
            f"**Code:** `{_MODULE_PATH}.SpotViewSet_create`"            
        )
    ),
    update=extend_schema(
        summary="Actualizar spot completo",
        tags=["spots"],
        description=(
            "Actualiza todos los campos de un spot. \n\n"
            "Solo el propietario del spot o un administrador pueden actualizarlo.\n\n"
            f"**Code:** `{_MODULE_PATH}.SpotViewSet_update`"            
        )
    ),
    partial_update=extend_schema(
        summary="Actualizar spot parcialmente",
        tags=["spots"],
        description=(
            "Actualiza uno o más campos de un spot. \n\n"
            "Solo el propietario del spot o un administrador pueden actualizarlo. \n\n"
            f"**Code:** `{_MODULE_PATH}.SpotViewSet_create`"            
        )
    ),
    destroy=extend_schema(
        summary="Eliminar spot",
        tags=["spots"],
        description=(
            "Elimina un spot del sistema (soft delete).\n\n "
            "Solo el propietario o un administrador pueden eliminarlo.\n\n"
            f"**Code:** `{_MODULE_PATH}.SpotViewSet_destroy`"                        
        )
    )
)
class SpotViewSet(ViewSetSentryMixin, viewsets.ModelViewSet):
    serializer_class = SpotSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action == 'list':
            return []  

        # Todo lo demas sigue requiriendo autenticacion
        return [permission() for permission in self.permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Spot.objects.filter(deleted_at__isnull=True)
                
        if self.action == 'list':
            if user.is_staff:
                status_param = self.request.query_params.get('status')
                if status_param:
                    queryset = queryset.filter(status__key=status_param)
            else:
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
    
    @extend_schema(
        summary="Autorizar spot",
        tags=["spots"],
        description=(
            "Autoriza un spot cambiando su estado a APPROVED. \n\n"
            "Solo accesible para administradores. \n\n"
            "El spot se activa automáticamente al ser aprobado.\n\n"
            f"**Code:** `{_MODULE_PATH}.SpotViewSet_authorize`"            
        ),
        responses={
            200: SpotSerializer,
            403: OpenApiResponse(description="No tienes permisos de administrador"),
            404: OpenApiResponse(description="Spot no encontrado")
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def authorize(self, request, pk=None):
        """Autorizar un spot"""
        spot = self.get_object()
        spot.status_id = models.get_approved()  
        spot.is_active = True
        spot.reviewed_user = request.user
        spot.reviewed_at = timezone.now()
        spot.save()
        
        serializer = self.get_serializer(spot)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Rechazar spot",
        tags=["spots"],
        description=(
            "Rechaza un spot cambiando su estado a REJECTED.\n\n "
            "Solo accesible para administradores. \n\n"
            "Se requiere proporcionar una razón para el rechazo.\n\n"
            f"**Code:** `{_MODULE_PATH}.SpotViewSet_deny`"                        
        ),
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'reason': {
                        'type': 'string',
                        'description': 'Razón del rechazo'
                    }
                },
                'required': ['reason']
            }
        },
        responses={
            200: SpotSerializer,
            400: OpenApiResponse(description="Se requiere una razón para rechazar"),
            403: OpenApiResponse(description="No tienes permisos de administrador"),
            404: OpenApiResponse(description="Spot no encontrado")
        }
    )
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
    
    @extend_schema(
        summary="Mis spots",
        tags=["spots"],
        description=(
            "Obtiene todos los spots creados por el usuario autenticado, \n\n "
            "en cualquier estado (pendiente, aprobado o rechazado). \n\n"
            f"**Code:** `{_MODULE_PATH}.SpotViewSet_my_spots`"                                    
        ),
        responses={
            200: SpotSerializer(many=True)
        }
    )
    @action(detail=False, methods=['get'])
    def my_spots(self, request):
        """Spots del usuario actual"""
        queryset = Spot.objects.filter(
            user=request.user,
            deleted_at__isnull=True,
            is_active = True,
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Agregar a favoritos",
        tags=["spots", "favorite spots"],
        description=(
            "Agrega un spot a la lista de favoritos del usuario. \n\n"
            "Si el spot ya está en favoritos pero inactivo, lo reactiva.\n\n"
            f"**Code:** `{_MODULE_PATH}.SpotViewSet_add_to_favorites`"                                                
        ),
        responses={
            201: OpenApiResponse(
                description="Spot agregado a favoritos",
                response={'type': 'object', 'properties': {'status': {'type': 'string'}}}
            ),
            200: OpenApiResponse(
                description="Spot ya estaba en favoritos o fue reactivado",
                response={'type': 'object', 'properties': {'status': {'type': 'string'}}}
            )
        }
    )
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
    
    @extend_schema(
        summary="Remover de favoritos",
        tags=["spots", "favorite spots"],
        description=(
            "Remueve un spot de la lista de favoritos del usuario (soft delete). \n\n"
            "El spot no se elimina, solo se marca como inactivo en favoritos.\n\n"
            f"**Code:** `{_MODULE_PATH}.SpotViewSet_remove_from_favorites`"                                                
        ),
        responses={
            200: OpenApiResponse(
                description="Spot removido de favoritos",
                response={'type': 'object', 'properties': {'status': {'type': 'string'}}}
            ),
            404: OpenApiResponse(description="Este spot no está en tus favoritos")
        }
    )
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


@extend_schema(
    summary="Listar mis favoritos",
    tags=["favorite spots"],
    description=(
        "Obtiene la lista de spots favoritos del usuario autenticado. \n\n"
        "Solo muestra favoritos activos y spots no eliminados.\n\n"
        f"**Code:** `{_MODULE_PATH}.UserFavoriteSpotsView`"                                                
    ),
    responses={
        200: UserFavoriteSpotSerializer(many=True)
    }
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


@extend_schema_view(
    list=extend_schema(
        summary="Listar captions",
        tags=["spot-captions"],
        description=(
            "Obtiene la lista de captions (fotos) del spot compartido en el primer parametro de ruta.\n\n "
            f"**Code:** `{_MODULE_PATH}.SpotCaptionViewSet_list`"                                                            
        ),
        parameters=[
            OpenApiParameter(
                name='spot',
                type=int,
                location=OpenApiParameter.QUERY,
                description='ID del spot para filtrar sus captions',
                required=False
            )
        ]
    ),
    retrieve=extend_schema(
        summary="Obtener caption",
        tags=["spot-captions"],
        description="Obtiene los detalles de un caption específico por su ID. \n\n"
                    f"**Code:** `{_MODULE_PATH}.SpotCaptionViewSet_list`"                                                            
    ),
    create=extend_schema(
        summary="Crear caption",
        tags=["spot-captions"],
        description=(
            "Crea un nuevo caption (comentario) para un spot. \n\n"
            "El caption se asocia automáticamente al usuario autenticado. \n\n"
            "El ID del spot debe ser proporcionado en la URL como parametro de ruta.\n\n"
            f"**Code:** `{_MODULE_PATH}.SpotCaptionViewSet_create`"                                                            
        )
    )
)
class SpotCaptionViewSet(ViewSetSentryMixin, viewsets.ModelViewSet):
    """
    ViewSet para manejar los captions de spots
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
        print("KWARGS:", self.kwargs)
        spot_id = self.kwargs.get('spot_pk')
        
        spot = get_object_or_404(Spot, pk=spot_id, is_active=True)
        
        if not spot_id:
            raise ValidationError("URL inválida: falta el spot_id")

        serializer.save(
            user=self.request.user,
            spot=spot
        )
    
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