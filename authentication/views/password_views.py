"""
Vistas para restablecimiento de contraseña.
"""
from rest_framework import generics, status
from authentication.base import BaseAuthenticationView
from authentication.docs.schemas import CHANGE_PASSWORD, PASSWORD_RESET_CONFIRM, PASSWORD_RESET_REQUEST
from authentication.serializers import (
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    SetNewPasswordSerializer
)
from authentication.services import PasswordResetService, ChangePasswordService
from drf_spectacular.utils import extend_schema

from core.docs.schema_utils import auto_schema
from core.responses.messages import AuthMessages, UserMessages
from rest_framework.permissions import IsAuthenticated

@auto_schema(**PASSWORD_RESET_REQUEST)
class PasswordResetRequestView(BaseAuthenticationView, generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    sentry_operation_name = "password_reset_request"
    sentry_operation_name = "sensitive"

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

@auto_schema(**PASSWORD_RESET_CONFIRM)
class PasswordResetConfirmView(BaseAuthenticationView, generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    sentry_operation_name = "password_reset_confirm"
    sentry_operation_name = "sensitive"

    def post(self, request):
        return self.handle_with_sentry(
            operation=self._confirm_reset_password,
            request=request,
            tags={
                'app': 'authentication',
                'component': 'PasswordResetConfirmView',
            },
            success_message={'detail': AuthMessages.PASSWORD_RESET_SUCCESS},
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

@auto_schema(**CHANGE_PASSWORD)
class ChangePasswordView(BaseAuthenticationView, generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    sentry_operation_name = "change_password"
    sentry_sensitivity = "sensitive"

    def post(self, request):
        return self.handle_with_sentry(
            operation=self._change_password,
            request=request,
            tags={
                'app': 'authentication',
                'component': 'ChangePasswordView',
            },
            success_message={'detail': AuthMessages.PASSWORD_CHANGED_SUCCESS},
            success_status=status.HTTP_200_OK
        )

    def _change_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ChangePasswordService.change_password(
            user=request.user,
            current_password=serializer.validated_data['current_password'],
            new_password=serializer.validated_data['new_password'],
        )

        self.log_auth_event(
            'password_changed',
            user=request.user,
            success=True
        )