from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics,permissions
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from django.contrib.auth import get_user_model

User = get_user_model()
from core.mixins import  ViewSetSentryMixin
from core.permission import IsOwnerOrAdmin, IsOwnerOrReadOnly
from spots_routes.filters import RouteFilter, RoutePhotoFilter, SpotFilter
from spots_routes.models import Route, RoutePhoto, Spot, SpotCaption, SpotStatusReview, UserFavoriteRoute, UserFavoriteSpot
from spots_routes.serializer import (
    SpotCaptionCreateSerializer, 
    SpotCaptionSerializer, 
    SpotSerializer,
    SpotUpdateSerializer, 
    UserFavoriteSpotSerializer,
    RouteSerializer, 
    RoutePhotoSerializer, 
    RoutePhotoCreateSerializer,
    UserFavoriteRouteSerializer
)
from drf_spectacular.types import OpenApiTypes
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from spots_routes import models
from spots_routes.docs.params import ROUTE_FILTER_PARAMS, ROUTE_PHOTO_FILTER_PARAMS, NESTED_PATH_PARAMS
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
class SpotViewSet(ViewSetSentryMixin,  viewsets.ModelViewSet):
    serializer_class = SpotSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = SpotFilter
    
    def get_permissions(self): 
            """Permisos dinámicos según la acción"""
            if self.action == 'list':
                return [] 
            
            if self.action in ['update', 'partial_update', 'destroy']: 
                return [IsAuthenticated(), IsOwnerOrAdmin()] 
                       
            return [permission() for permission in self.permission_classes]
    
    def get_queryset(self):
        user = self.request.user

        queryset = Spot.objects

        if self.action in ("list", "retrieve"):
            if not user.is_staff:
                queryset = queryset.filter(
                    is_active=True,
                    status__key="APPROVED"
                )

        return queryset.order_by("-created_at")
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return SpotUpdateSerializer
        return SpotSerializer
    
    def perform_create(self, serializer):
        """Asignar usuario y estado inicial al crear"""
        serializer.save(
            user=self.request.user,
            status_id=models.get_default_pending()
        )

    @extend_schema(
        summary="Autorizar spot",
        tags=["spots"],
        request= None,
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
        ).order_by('-created_at')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Agregar a favoritos",
        tags=["spots", "spots-favorite"],
        request= None,
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
        tags=["spots", "spots-favorite"],
        request= None,
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
        summary="Agregar/Quitar favorito",
        tags=["spots", "spots-favorite"],
        request=None,
        description="Maneja el estado de favorito del spot (toggle)"
    )
    @action(detail=True, methods=['post', 'delete'], url_path='favorites')
    def favorites(self, request, pk=None):
        spot = self.get_object()
        
        if request.method == 'POST':
            favorite, created = UserFavoriteSpot.objects.get_or_create(
                user=request.user,
                spot=spot,
                defaults={'is_active': True}
            )
            
            if not created:
                if not favorite.is_active:
                    favorite.is_active = True
                    favorite.save()
                    return Response(
                        {'status': 'added'},
                        status=status.HTTP_200_OK
                    )
                return Response(
                    {'status': 'already_exists'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                {'status': 'added'},
                status=status.HTTP_201_CREATED
            )
        
        elif request.method == 'DELETE':
            try:
                favorite = UserFavoriteSpot.objects.get(
                    user=request.user,
                    spot=spot,
                    is_active=True
                )
                favorite.is_active = False
                favorite.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except UserFavoriteSpot.DoesNotExist:
                return Response(
                    {'detail': 'No está en favoritos'},
                    status=status.HTTP_404_NOT_FOUND
                )
    
@extend_schema(
    summary="Listar mis favoritos",
    tags=["spots-favorite"],
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
            spot__is_active =True,
            spot__status__key = "APPROVED"
        ).select_related('spot').order_by('-created_at')


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
    ),
    update=extend_schema(
        summary="Actualizar caption completo",
        tags=["spot-captions"],
        description=(
            "Actualiza todos los campos de un caption.\n\n"
            "Solo el propietario del caption o un administrador pueden actualizarlo.\n\n"
            f"**Code:** `{_MODULE_PATH}.SpotCaptionViewSet_update`"
        ),
        responses={
            200: SpotCaptionSerializer,
            403: OpenApiResponse(description="No tienes permisos para editar este caption"),
            404: OpenApiResponse(description="Caption no encontrado")
        }
    ),
    partial_update=extend_schema(
        summary="Actualizar caption parcialmente",
        tags=["spot-captions"],
        description=(
            "Actualiza uno o más campos de un caption.\n\n"
            "Solo el propietario del caption o un administrador pueden actualizarlo.\n\n"
            f"**Code:** `{_MODULE_PATH}.SpotCaptionViewSet_partial_update`"
        ),
        responses={
            200: SpotCaptionSerializer,
            403: OpenApiResponse(description="No tienes permisos para editar este caption"),
            404: OpenApiResponse(description="Caption no encontrado")
        }
    ),
    destroy=extend_schema(
        summary="Eliminar caption",
        tags=["spot-captions"],
        description=(
            "Elimina un caption. Solo el propietario o un administrador pueden eliminarlo.\n\n"
            "Este endpoint realizará la eliminación del registro.\n\n"
            f"**Code:** `{_MODULE_PATH}.SpotCaptionViewSet_destroy`"
        ),
        responses={
            204: OpenApiResponse(description="Caption eliminado correctamente"),
            403: OpenApiResponse(description="No tienes permisos para eliminar este caption"),
            404: OpenApiResponse(description="Caption no encontrado")
        }
    )
)
class SpotCaptionViewSet(ViewSetSentryMixin, viewsets.ModelViewSet):
    """
    ViewSet para manejar los captions de spots
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
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
        

#====================================== ROUTES =================================================

@extend_schema_view(
    list=extend_schema(
        summary="Listar rutas",
        tags=["routes"],
        description=(
            "Obtiene una lista de todas las rutas activas.\n\n"
            "- Soporta filtrado mediante query params\n"
            "- Por defecto no incluye fotos (optimización de rendimiento)\n"
            "- Use `?expand=photos` para incluir fotos en la respuesta\n"
            "- Requiere autenticación solo para crear/editar\n\n"
            f"**Code:** `{_MODULE_PATH}.RouteViewSet_list`"
        ),
        parameters=ROUTE_FILTER_PARAMS
    ),
    retrieve=extend_schema(
        summary="Obtener detalle de ruta",
        tags=["routes"],
        description=(
            "Obtiene los detalles completos de una ruta específica, incluyendo fotos.\n\n"
            f"**Code:** `{_MODULE_PATH}.RouteViewSet_retrieve`"
        )
    ),
    create=extend_schema(
        summary="Crear nueva ruta",
        tags=["routes"],
        description=(
            "Crea una nueva ruta asociada a un spot.\n\n"
            "**Notas:**\n"
            "- El usuario se asigna automáticamente del token de autenticación\n"
            "- El spot se obtiene del parámetro de la URL (spot_pk)\n"
            "- Requiere autenticación\n\n"
            f"**Code:** `{_MODULE_PATH}.RouteViewSet_create`"
        )
    ),
    update=extend_schema(
        summary="Actualizar ruta completa",
        tags=["routes"],
        description=(
            "Actualiza todos los campos de una ruta. Solo el propietario puede editar.\n\n"
            f"**Code:** `{_MODULE_PATH}.RouteViewSet_update`"
        )
    ),
    partial_update=extend_schema(
        summary="Actualizar ruta parcialmente",
        tags=["routes"],
        description=(
            "Actualiza campos específicos de una ruta. Solo el propietario puede editar.\n\n"
            f"**Code:** `{_MODULE_PATH}.RouteViewSet_partial_update`"
        )
    ),
    destroy=extend_schema(
        summary="Eliminar ruta (soft delete)",
        tags=["routes"],
        description=(
            "Marca la ruta como inactiva en lugar de eliminarla permanentemente.\n\n"
            "Solo el propietario puede eliminar su ruta.\n\n"
            f"**Code:** `{_MODULE_PATH}.RouteViewSet_destroy`"
        )
    )
)
class RouteViewSet(ViewSetSentryMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar las rutas.
    Permite CRUD completo y acciones personalizadas.
    """
    queryset = Route.objects.filter(is_active=True).select_related(
        'user', 'difficulty', 'travel_mode', 'spot'
    ).prefetch_related('photo').order_by('-created_at')
    serializer_class = RouteSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    
    filter_backends = [DjangoFilterBackend]
    filterset_class = RouteFilter
    
    def get_queryset(self):
        queryset = Route.objects.filter(is_active=True).select_related(
            'user', 'difficulty', 'travel_mode', 'spot'
        )
        
        # Solo cargar fotos si:
        # 1. Es accion retrieve O
        # 2. Se solicita explicitamente con ?expand=photos
        expand = self.request.query_params.get('expand', '')
        if self.action == 'retrieve' or 'photos' in expand.split(','):
            queryset = queryset.prefetch_related('photo')
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """
        Retorna un serializer dinámico según la acción y query params.
        """
        if self.action == 'list':
            expand = self.request.query_params.get('expand', '')
            if 'photos' not in expand.split(','):
                return self._get_list_serializer_without_photos()
        
        return RouteSerializer
    
    def _get_list_serializer_without_photos(self):
        """
        Crea un serializer ligero sin fotos para listados.
        """
        class RouteLightSerializer(RouteSerializer):
            class Meta(RouteSerializer.Meta):
                fields = [f for f in RouteSerializer.Meta.fields if f != 'route_photos']
        
        return RouteLightSerializer
    
    def perform_create(self, serializer):
        """
        Asigna automáticamente el usuario autenticado al crear una ruta y el spot del path.
        """
        spot_id = self.kwargs.get('spot_pk')
        spot = get_object_or_404(Spot, pk=spot_id, is_active=True)
        serializer.save(
            user=self.request.user,
            spot=spot
        )    
    
    def perform_destroy(self, instance):
        """
        Soft delete - marca como inactiva en lugar de eliminar.
        """
        instance.is_active = False
        instance.save()
    
    @extend_schema(
        summary="Añadir ruta a favoritos",
        tags=["routes", "routes-favorite"],
        description=(
            "Marca una ruta como favorita para el usuario autenticado.\n\n"
            "**Comportamiento:**\n"
            "- Si ya existe como favorito pero estaba inactivo, lo reactiva\n"
            "- Si ya está activo, retorna error 400\n"
            "- Requiere autenticación\n\n"
            f"**Code:** `{_MODULE_PATH}.RouteViewSet_add_favorite`"
        ),
        responses={
            200: OpenApiResponse(description="Ruta reactivada en favoritos"),
            201: OpenApiResponse(description="Ruta añadida a favoritos exitosamente"),
            400: OpenApiResponse(description="La ruta ya está en favoritos"),
            401: OpenApiResponse(description="No autenticado"),
            404: OpenApiResponse(description="Ruta no encontrada"),
        },
        request=None,
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_favorite(self, request, pk=None, *args, **kwargs):
        """
        Añade la ruta a favoritos del usuario.
        """
        route = self.get_object()
        
        # Verificar si ya existe como favorito
        favorite, created = UserFavoriteRoute.objects.get_or_create(
            user=request.user,
            route=route,
            defaults={'is_active': True}
        )
        
        if not created:
            # Si ya existía, asegurarse de que esté activo
            if not favorite.is_active:
                favorite.is_active = True
                favorite.save()
                return Response(
                    {'message': 'Ruta añadida a favoritos'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'message': 'Esta ruta ya está en tus favoritos'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {'message': 'Ruta añadida a favoritos'},
            status=status.HTTP_201_CREATED
        )
    
    @extend_schema(
        summary="Eliminar ruta de favoritos",
        tags=["routes", "routes-favorite"],
        description=(
            "Elimina una ruta de los favoritos del usuario (soft delete).\n\n"
            "**Comportamiento:**\n"
            "- Marca el favorito como inactivo\n"
            "- Si no existe o ya está inactivo, retorna 404\n"
            "- Requiere autenticación\n\n"
            f"**Code:** `{_MODULE_PATH}.RouteViewSet_remove_favorite`"
        ),
        responses={
            200: OpenApiResponse(description="Ruta eliminada de favoritos exitosamente"),
            401: OpenApiResponse(description="No autenticado"),
            404: OpenApiResponse(description="La ruta no está en favoritos"),
        },
        request=None,
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def remove_favorite(self, request, pk=None, *args, **kwargs):
        """
        Elimina la ruta de favoritos del usuario.
        """
        route = self.get_object()
        
        try:
            favorite = UserFavoriteRoute.objects.get(
                user=request.user,
                route=route,
                is_active=True
            )
            favorite.is_active = False
            favorite.save()
            
            return Response(
                {'message': 'Ruta eliminada de favoritos'},
                status=status.HTTP_200_OK
            )
        except UserFavoriteRoute.DoesNotExist:
            return Response(
                {'message': 'Esta ruta no está en tus favoritos'},
                status=status.HTTP_404_NOT_FOUND
            )

@extend_schema_view(
    list=extend_schema(
        summary="Listar fotos de rutas",
        parameters=NESTED_PATH_PARAMS + ROUTE_PHOTO_FILTER_PARAMS,
        tags=["routes-photos"],
        description=(
            "Obtiene una lista de todas las fotos de rutas de un spot indicado en el query paramter\n\n"
            "Soporta filtrado por ruta, usuario, etc.\n\n"
            f"**Code:** `{_MODULE_PATH}.RoutePhotoViewSet_list`"
        )
    ),
    retrieve=extend_schema(
        summary="Obtener detalle de foto",
        parameters=NESTED_PATH_PARAMS,
        tags=["routes-photos"],
        description=(
            "Obtiene los detalles de una foto específica.\n\n"
            f"**Code:** `{_MODULE_PATH}.RoutePhotoViewSet_retrieve`"
        )
    ),
    create=extend_schema(
        summary="Subir nueva foto a ruta",
        tags=["routes-photos"],
        parameters=NESTED_PATH_PARAMS,
        description=(
            "Sube una nueva foto asociada a una ruta.\n\n"
            "- El usuario se asigna automáticamente\n"
            "- Debe incluir el ID de la ruta como parámetro de ruta\n"
            "- Requiere autenticación\n"
            "- Formato: multipart/form-data para subir imagen\n\n"
            f"**Code:** `{_MODULE_PATH}.RoutePhotoViewSet_create`"
        )
    ),
    update=extend_schema(
        summary="Actualizar foto de ruta (completo)",
        tags=["routes-photos"],
        parameters=NESTED_PATH_PARAMS,
        description=(
            "Actualiza todos los campos de una foto de ruta.\n\n"
            "Solo el propietario de la foto o un administrador pueden actualizarla.\n\n"
            f"**Code:** `{_MODULE_PATH}.RoutePhotoViewSet_update`"
        ),
        responses={
            200: RoutePhotoSerializer,
            403: OpenApiResponse(description="No tienes permisos para editar esta foto"),
            404: OpenApiResponse(description="Foto no encontrada")
        }
    ),
    partial_update=extend_schema(
        summary="Actualizar foto de ruta (parcial)",
        tags=["routes-photos"],
        parameters=NESTED_PATH_PARAMS,
        description=(
            "Actualiza uno o más campos de una foto de ruta.\n\n"
            "Solo el propietario de la foto o un administrador pueden actualizarla.\n\n"
            f"**Code:** `{_MODULE_PATH}.RoutePhotoViewSet_partial_update`"
        ),
        responses={
            200: RoutePhotoSerializer,
            403: OpenApiResponse(description="No tienes permisos para editar esta foto"),
            404: OpenApiResponse(description="Foto no encontrada")
        }
    ),
    destroy=extend_schema(
        summary="Eliminar foto de ruta",
        tags=["routes-photos"],
        parameters=NESTED_PATH_PARAMS,
        description=(
            "Elimina una foto de ruta. Solo el propietario o un administrador pueden eliminarla.\n\n"
            "La operación eliminará el recurso correspondiente.\n\n"
            f"**Code:** `{_MODULE_PATH}.RoutePhotoViewSet_destroy`"
        ),
        responses={
            204: OpenApiResponse(description="Foto eliminada correctamente"),
            403: OpenApiResponse(description="No tienes permisos para eliminar esta foto"),
            404: OpenApiResponse(description="Foto no encontrada")
        }
    )
)
class RoutePhotoViewSet(ViewSetSentryMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar las fotos de rutas.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RoutePhotoFilter
    
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return RoutePhoto.objects.none()

        queryset = RoutePhoto.objects.select_related('user', 'route')

        route_id = self.kwargs.get('route_pk')
        spot_id = self.kwargs.get('spot_pk')

        if route_id:
            queryset = queryset.filter(
                route_id=route_id,
                route__spot_id=spot_id,
                route__is_active=True
            ).order_by('-created_at')

        if self.action == "my_photos":
            queryset = queryset.filter(user=self.request.user)

        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """
        Usa diferentes serializers según la acción.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return RoutePhotoCreateSerializer
        return RoutePhotoSerializer
    
    def perform_create(self, serializer):
        route_id = self.kwargs.get('route_pk')

        if not route_id:
            raise ValidationError({'route': 'Se requiere el ID de la ruta'})

        route = get_object_or_404(
            Route,
            id=route_id,
            spot_id=self.kwargs.get('spot_pk'),
            is_active=True
        )

        serializer.save(user=self.request.user, route=route)
    
    @extend_schema(
        summary="Obtener mis fotos",
        tags=["routes-photos"],
        parameters=NESTED_PATH_PARAMS,
        description=(
            "Obtiene solo las fotos subidas por el usuario autenticado.\n\n"
            "- Filtrado automático por usuario\n"
            "- Requiere autenticación\n"
            "- Incluye todas las relaciones (ruta, usuario)\n\n"
            f"**Code:** `{_MODULE_PATH}.RoutePhotoViewSet_my_photos`"
        ),
        responses={
            200: RoutePhotoSerializer(many=True),
            401: OpenApiResponse(description="No autenticado"),
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_photos(self, request):
        """
        Obtiene solo las fotos del usuario autenticado.
        """
        photos = self.get_queryset().filter(user=request.user).order_by('-created_at')
        serializer = self.get_serializer(photos, many=True)
        return Response(serializer.data)

@extend_schema(
    summary="Listar rutas favoritas del usuario",
    description=(
        "Obtiene la lista de rutas marcadas como favoritas por el usuario autenticado."
        "- Solo muestra favoritos activos""- Requiere autenticación"
        "- Incluye información completa de cada ruta"
        f"**Code:** `{_MODULE_PATH}.UserFavoriteRouteView`"
    ),
    tags=['routes-favorite'],
    responses={
        200: OpenApiResponse(description="Lista de rutas favoritas"),
        401: OpenApiResponse(description="No autenticado"),
    }
)
class UserFavoriteRouteView(generics.ListAPIView):
    """
    Vista para listar las rutas favoritas del usuario.
    """
    serializer_class = UserFavoriteRouteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserFavoriteRoute.objects.filter(
            user=self.request.user,
            is_active=True,
            route__deleted_at__isnull=True
        ).select_related('route').order_by('-created_at')