from django.urls import include, path
from spots_routes.views import SpotCaptionViewSet, SpotViewSet, UserFavoriteSpotsView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'spots', SpotViewSet, basename='spots')
router.register(r'spots/captions', SpotCaptionViewSet, basename='spots_captions')

spots_routes_patterns = ([
    path('', include(router.urls)),
    path('spots/favorites/', UserFavoriteSpotsView.as_view(), name='user_favorite_spots'),
], 'spots_routes')