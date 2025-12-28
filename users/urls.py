from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UpdateProfileThumbView, UserViewSet, confirm_user
from rest_framework_nested.routers import NestedDefaultRouter

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

user_patterns = ([
    path('confirm-user/', confirm_user, name='verify-email'),
    path('profile/thumb/', UpdateProfileThumbView.as_view(), name='profile-thumb'),
    path('', include(router.urls)),
], 'users')