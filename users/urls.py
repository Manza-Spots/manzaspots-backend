from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileView, UserViewSet, verify_email

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')
user_patterns = ([
    path('verify-email/', verify_email, name='verify-email'),
    path('profile/', UserProfileView.as_view(), name='verify-email'),    
    path('', include(router.urls)),
], 'users')