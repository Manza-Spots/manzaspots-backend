"""
URLs de autenticación organizadas por tipo.
"""
from django.urls import path
from authentication.views.jwt_views import (
    LoginView, LogoutView, TokenRefreshView, TokenVerifyView
)
from authentication.views.oauth_views import (
    GoogleLoginView, FacebookLoginView
)
from authentication.views.password_views import (
    PasswordResetRequestView, PasswordResetConfirmView
)
from authentication.views.user_views import  RegistrationAPIView, ResendTokenAPIView, VerifyEmailAPIView

authentications_patterns = ([
    # ========== JWT Authentication ==========
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # ========== OAuth Social Login ==========
    path('oauth/google/', GoogleLoginView.as_view(), name='google_login'),
    path('oauth/facebook/', FacebookLoginView.as_view(), name='facebook_login'),
    
    # ========== Password Management ==========
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # ========== Register User ============
    path('register/', RegistrationAPIView.as_view(), name='register'),
    path('email/verify/', VerifyEmailAPIView.as_view(), name='confirm_user'),
    path('resend-token/', ResendTokenAPIView.as_view(), name='resend_token')
], 'auth')