from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmailUpdateAPIView, UpdateProfileThumbView, UserViewSet
from rest_framework_nested.routers import NestedDefaultRouter

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

user_patterns = ([
    path('profile/thumb/', UpdateProfileThumbView.as_view(), name='profile-thumb'),
    path('me/email/request-change', EmailUpdateAPIView.as_view(), name='request_update_email'),
    path('', include(router.urls)),
], 'users')