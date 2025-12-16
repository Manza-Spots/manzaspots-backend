from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileView, UserViewSet, confirm_user

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')
user_patterns = ([
    path('confirm-user/', confirm_user, name='verify-email'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),    
    path('', include(router.urls)),
], 'users')