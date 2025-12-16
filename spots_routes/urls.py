from django.urls import include, path
from spots_routes.views import SpotCaptionViewSet, SpotViewSet, UserFavoriteSpotsView
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

router = DefaultRouter()
router.register(r'spots', SpotViewSet, basename='spots')

# Recursos anidados bajo spots
spots_router = NestedDefaultRouter(router, r'spots', lookup='spot')
spots_router.register(r'captions', SpotCaptionViewSet, basename='spot-captions')
# spots_router.register(r'routes', RouteViewSet, basename='spot-routes')

# Recursos anidados bajo routes
# routes_router = NestedDefaultRouter(spots_router, r'routes', lookup='route')
# routes_router.register(r'photos', RoutePhotoViewSet, basename='route-photos')

spots_routes_patterns = ([
    path('spots/favorites/', UserFavoriteSpotsView.as_view(), name='user_favorite_spots'),
    path('', include(router.urls)),
    path('', include(spots_router.urls)),
    # path('', include(routes_router.urls)),
], 'spots_routes')