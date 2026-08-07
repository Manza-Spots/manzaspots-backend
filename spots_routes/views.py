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

from spots_routes.docs.schema import (ROUTE_PHOTO_CREATE, ROUTE_PHOTO_DESTROY, ROUTE_PHOTO_LIST, ROUTE_PHOTO_MY_PHOTOS, ROUTE_PHOTO_PARTIAL_UPDATE, ROUTE_PHOTO_RETRIEVE, ROUTE_PHOTO_UPDATE, SPOT_CAPTION_CREATE, SPOT_CAPTION_DESTROY, SPOT_CAPTION_LIST, SPOT_CAPTION_PARTIAL_UPDATE, SPOT_CAPTION_RETRIEVE, SPOT_CAPTION_UPDATE, USER_FAVORITE_ROUTES_LIST, USER_FAVORITE_SPOTS_LIST,SPOT_CREATE, SPOT_LIST, SPOT_RETRIEVE,
SPOT_UPDATE,
    SPOT_PARTIAL_UPDATE,
    SPOT_DESTROY,
    SPOT_AUTHORIZE,
    SPOT_DENY,
    SPOT_MY_SPOTS,
    SPOT_ADD_TO_FAVORITES,
    SPOT_REMOVE_FROM_FAVORITES,
    SPOT_FAVORITES,
    ROUTE_LIST,
    DIFFICULTY_RETRIEVE,
    ROUTE_RETRIEVE,
    ROUTE_CREATE,
    ROUTE_UPDATE,
    ROUTE_PARTIAL_UPDATE,
    ROUTE_DESTROY,
    ROUTE_ADD_FAVORITE,
    ROUTE_REMOVE_FAVORITE,
    DIFFICULTY_LIST,
    DIFFICULTY_LIST,
    TRAVEL_MODE_LIST,
    TRAVEL_MODE_RETRIEVE)

User = get_user_model()
from core.docs.schema_utils import auto_schema, auto_schema_view
from core.mixins import  ViewSetSentryMixin
from core.permission import IsOwnerOrAdmin, IsOwnerOrReadOnly
from spots_routes.filters import RouteFilter, RoutePhotoFilter, SpotFilter
from spots_routes.models import Difficulty, Route, RoutePhoto, Spot, SpotCaption, SpotStatusReview, TravelMode, UserFavoriteRoute, UserFavoriteSpot
from spots_routes.serializer import (
    DifficultySerializer,
    SpotCaptionCreateSerializer, 
    SpotCaptionSerializer, 
    SpotSerializer,
    SpotUpdateSerializer,
    TravelModeSerializer, 
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

@auto_schema_view(
    list=SPOT_LIST,
    retrieve=SPOT_RETRIEVE,
    create=SPOT_CREATE,
    update=SPOT_UPDATE,
    partial_update=SPOT_PARTIAL_UPDATE,
    destroy=SPOT_DESTROY,
    authorize=SPOT_AUTHORIZE,
    deny=SPOT_DENY,
    my_spots=SPOT_MY_SPOTS,
    add_to_favorites=SPOT_ADD_TO_FAVORITES,
    remove_from_favorites=SPOT_REMOVE_FROM_FAVORITES,
    favorites=SPOT_FAVORITES,
)
class SpotViewSet(ViewSetSentryMixin, viewsets.ModelViewSet):
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
        
        if self.action in ['authorize', 'deny']:
            return [IsAdminUser()]
        
        return [permission() for permission in self.permission_classes]
    
    def get_queryset(self):
        user = self.request.user

        queryset = Spot.objects

        if self.action in ("list", "retrieve"):
            if not user.is_authenticated or not user.is_staff:
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
            status=SpotStatusReview.objects.get(key='PENDING')
        )
    
    # ── Acciones personalizadas ────────────────────────────────────────────
    
    @action(detail=True, methods=['post'])
    def authorize(self, request, pk=None):
        """Autorizar un spot"""
        spot = self.get_object()
        spot.status = SpotStatusReview.objects.get(key='APPROVED')
        spot.is_active = True
        spot.reviewed_user = request.user
        spot.reviewed_at = timezone.now()
        spot.save()
        
        serializer = self.get_serializer(spot)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deny(self, request, pk=None):
        """Denegar un spot"""
        spot = self.get_object()
        reason = request.data.get('reason')
        
        if not reason:
            return Response(
                {'error': 'Se requiere una razón para rechazar'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        spot.status = SpotStatusReview.objects.get(key='REJECTED')
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
            deleted_at__isnull=True,
            is_active=True,
        ).order_by('-created_at')
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
            if not favorite.is_active:
                favorite.is_active = True
                favorite.save()
                return Response(
                    {'status': 'reactivated'}, 
                    status=status.HTTP_200_OK
                )
            return Response(
                {'status': 'already_favorited'},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {'status': 'added'}, 
            status=status.HTTP_201_CREATED
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
            return Response(
                {'status': 'removed'}, 
                status=status.HTTP_200_OK
            )
        except UserFavoriteSpot.DoesNotExist:
            return Response(
                {'error': 'Este spot no está en tus favoritos'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post', 'delete'], url_path='favorites')
    def favorites(self, request, pk=None):
        """Maneja el estado de favorito del spot (toggle)"""
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

@auto_schema(**USER_FAVORITE_SPOTS_LIST)
class UserFavoriteSpotsView(generics.ListAPIView):
    """Vista para listar favoritos del usuario actual"""
    serializer_class = UserFavoriteSpotSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserFavoriteSpot.objects.filter(
            user=self.request.user,
            is_active=True,
            spot__is_active=True,
            spot__status__key="APPROVED"
        ).select_related('spot').order_by('-created_at')




@auto_schema_view(
    list=SPOT_CAPTION_LIST,
    retrieve=SPOT_CAPTION_RETRIEVE,
    create=SPOT_CAPTION_CREATE,
    update=SPOT_CAPTION_UPDATE,
    partial_update=SPOT_CAPTION_PARTIAL_UPDATE,
    destroy=SPOT_CAPTION_DESTROY,
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
        
        if not spot_id:
            raise ValidationError("URL inválida: falta el spot_id")
        
        spot = get_object_or_404(Spot, pk=spot_id, is_active=True)
        
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
@auto_schema_view(
    list=ROUTE_LIST,
    retrieve=ROUTE_RETRIEVE,
    create=ROUTE_CREATE,
    update=ROUTE_UPDATE,
    partial_update=ROUTE_PARTIAL_UPDATE,
    destroy=ROUTE_DESTROY,
    add_favorite=ROUTE_ADD_FAVORITE,
    remove_favorite=ROUTE_REMOVE_FAVORITE,
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
        # 1. Es acción retrieve O
        # 2. Se solicita explícitamente con ?expand=photos
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
    
    # ── Acciones personalizadas ────────────────────────────────────────────
    
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


@auto_schema_view(
    list=ROUTE_PHOTO_LIST,
    retrieve=ROUTE_PHOTO_RETRIEVE,
    create=ROUTE_PHOTO_CREATE,
    update=ROUTE_PHOTO_UPDATE,
    partial_update=ROUTE_PHOTO_PARTIAL_UPDATE,
    destroy=ROUTE_PHOTO_DESTROY,
    my_photos=ROUTE_PHOTO_MY_PHOTOS,
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
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_photos(self, request):
        """
        Obtiene solo las fotos del usuario autenticado.
        """
        photos = self.get_queryset().filter(user=request.user).order_by('-created_at')
        serializer = self.get_serializer(photos, many=True)
        return Response(serializer.data)



@auto_schema(**USER_FAVORITE_ROUTES_LIST)
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
        
        
@auto_schema_view(
    list=DIFFICULTY_LIST,
    retrieve=DIFFICULTY_RETRIEVE,
)
class DifficultyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para consultar los niveles de dificultad.
    """
    queryset = Difficulty.objects.filter(is_active=True).order_by('name')
    serializer_class = DifficultySerializer
    permission_classes = [permissions.AllowAny]


@auto_schema_view(
    list=TRAVEL_MODE_LIST,
    retrieve=TRAVEL_MODE_RETRIEVE,
)
class TravelModeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para consultar los modos de viaje.
    """
    queryset = TravelMode.objects.filter(is_active=True).order_by('name')
    serializer_class = TravelModeSerializer
    permission_classes = [permissions.AllowAny]