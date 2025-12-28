from django.urls import include, path
import rest_framework_simplejwt.views as jwt_views

from authentication.views import DocumentedTokenBlacklistView, DocumentedTokenObtainPairView, DocumentedTokenRefreshView, DocumentedTokenVerifyView, GoogleLogin, PasswordResetConfirmView, PasswordResetRequestView

authentications_patterns = ([
    # url tokens
    path('login/', DocumentedTokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", DocumentedTokenRefreshView.as_view()),
    path("token/verify/", DocumentedTokenVerifyView.as_view()),
    path('logout/', DocumentedTokenBlacklistView.as_view(), name="logout"),
    
    # url recovery password
    path('reset-password/', PasswordResetRequestView.as_view(), name='reset-password'),
    path('reset-password-confirm/', PasswordResetConfirmView.as_view(), name='reset-password-confirm'),

    #url providers
    # path('accounts/', include('allauth.urls')),  
    # path('registration/', include('dj_rest_auth.registration.urls')),    
    path('google/', GoogleLogin.as_view(), name='google_login'),
    
    path("token/refresh/", DocumentedTokenRefreshView.as_view()),
    path("token/verify/", DocumentedTokenVerifyView.as_view()),

], "auth")