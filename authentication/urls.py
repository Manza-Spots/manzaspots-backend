from django.urls import include, path
import rest_framework_simplejwt.views as jwt_views

from authentication.views import DocumentedTokenBlacklistView, DocumentedTokenObtainPairView, DocumentedTokenRefreshView, DocumentedTokenVerifyView, FacebookLogin, GoogleLogin, PasswordResetConfirmView, PasswordResetRequestView

authentications_patterns = ([
    # Tokens
    path('login/', DocumentedTokenObtainPairView.as_view(), name="login"),
    path('logout/', DocumentedTokenBlacklistView.as_view(), name="logout"),
    path("token/refresh/", DocumentedTokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", DocumentedTokenVerifyView.as_view(), name="token_verify"),
    
    # Password Recovery
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # OAuth Providers
    path('oauth/google/', GoogleLogin.as_view(), name='google_login'),
    path('oauth/facebook/', FacebookLogin.as_view(), name='facebook_login'),
], "auth")