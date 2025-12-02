from django.urls import include, path
import rest_framework_simplejwt.views as jwt_views

from authentication.views import GoogleLogin, PasswordResetConfirmView, PasswordResetRequestView

authentications_patterns = ([
    # url tokens
    path('login/', jwt_views.TokenObtainPairView.as_view(), name="login"),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name="refresh_token"),
    path('token/verify/', jwt_views.TokenVerifyView.as_view(), name="verify_token"),
    path('logout/', jwt_views.TokenBlacklistView.as_view(), name="logout"),
    
    # url recovery password
    path('reset-password/', PasswordResetRequestView.as_view(), name='reset-password'),
    path('reset-password-confirm/', PasswordResetConfirmView.as_view(), name='reset-password-confirm'),

    #url providers
    # path('accounts/', include('allauth.urls')),  
    path('registration/', include('dj_rest_auth.registration.urls')),    
    path('google/', GoogleLogin.as_view(), name='google_login'),
], "auth")