"""
Vistas para restablecimiento de contraseña.
"""
from rest_framework import generics, status
from authentication.base import BaseAuthenticationView
from authentication.docs.schemas import PASSWORD_RESET_CONFIRM, PASSWORD_RESET_REQUEST
from authentication.serializers import (
    PasswordResetRequestSerializer,
    SetNewPasswordSerializer
)
from authentication.services import PasswordResetService
from drf_spectacular.utils import extend_schema

from core.responses.messages import AuthMessages, UserMessages

_MODULE_PATH = 'authentication.views.password_views'


@PASSWORD_RESET_REQUEST
class PasswordResetRequestView(BaseAuthenticationView, generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    sentry_operation_name = "password_reset_request"
    
    def post(self, request):
        return self.handle_with_sentry(
            operation=self._request_password_reset,
            request=request,
            tags={
                'app': 'authentication',
                'component': 'PasswordResetRequestView',
            },
            success_message={
                "detail": UserMessages.EMAIL_SENT_IF_EXISTS
            },
            success_status=status.HTTP_200_OK
        )
    
    def _request_password_reset(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        PasswordResetService.request_reset(email, request)
        
        # Log genérico (sin revelar si existe)
        self.log_auth_event(
            'password_reset_requested',
            success=True,
            email_provided=True
        )

@PASSWORD_RESET_CONFIRM
class PasswordResetConfirmView(BaseAuthenticationView, generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    sentry_operation_name = "password_reset_confirm"
    
    def post(self, request):
        return self.handle_with_sentry(
            operation=self._confirm_reset_password,
            request=request,
            tags={
                'app': 'authentication',
                'component': 'PasswordResetConfirmView',
            },
            success_message={'detail': AuthMessages.CONFIRM_NEW_PASSWORD},
            success_status=status.HTTP_200_OK
        )
    
    def _confirm_reset_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = PasswordResetService.confirm_reset(
            uidb64=serializer.validated_data['uidb64'],
            token=serializer.validated_data['token'],
            new_password=serializer.validated_data['new_password']
        )
        
        # Log del evento
        self.log_auth_event(
            'password_reset_completed',
            user=user,
            success=True
        )