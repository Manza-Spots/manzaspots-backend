import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes,authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth.models import User
from authentication.docs.schemas import REGISTRATION, RESEND_TOKEN, VERIFY_EMAIL, VERIFY_USER
from authentication.serializers import ResendTokenSerializer, UserCreateSerializer, VerifyEmailSerializer
from core.mixins import SentryErrorHandlerMixin, ViewSetSentryMixin
from manza_spots.throttling import RegisterThrottle, SensitiveOperationThrottle
from authentication.docs.request import RESEND_CONFIRMATION_EMAIL_REQUEST
from core.responses.messages import UserMessages
from core.services.email_service import ConfirmUserEmail
from django.conf import settings
from django.core.mail import send_mail
from authentication.services import UsersRegisterService
from rest_framework import viewsets, permissions, generics
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from rest_framework.mixins import (
    ListModelMixin,
    UpdateModelMixin
)
from django.contrib.auth import get_user_model
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView


_MODULE_PATH = __name__

@REGISTRATION
class RegistrationAPIView(SentryErrorHandlerMixin,CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserCreateSerializer
    throttle_classes =  [RegisterThrottle]

    
    def post(self, request, *args, **kwargs):
        return self.handle_with_sentry(
            operation=self._post,
            request=request,
            tags={
                'app': __name__,
                'authenticated': request.user.is_authenticated,
                'component': 'RegistrationAPIView._post',
            },
            success_message={
                'detail': UserMessages.USER_CREATED
            },
            success_status=status.HTTP_201_CREATED
        )
    
    def _post(self, request, *args, **kwargs):        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(is_active=False)  

        confirm_url= UsersRegisterService.get_confirmation_url(user, request)                    

        ConfirmUserEmail.send_email(
            to_email=user.email, 
            confirm_url=confirm_url, 
            nombre=user.username
        )
        self.logger.info(f'Se a creado el usuario inactivo {user.username}, y enviado el correo de confirmacion a {user.email}')

        headers = self.get_success_headers(serializer.data)
        return Response(
            {"detail": UserMessages.USER_CREATED},
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
@RESEND_TOKEN
class ResendTokenAPIView(SentryErrorHandlerMixin, CreateAPIView):
    permission_classes = [AllowAny]
    throttle_classes =  [SensitiveOperationThrottle]
    serializer_class = ResendTokenSerializer
    
    def post(self, request, *args, **kwargs):
        return self.handle_with_sentry(
            operation=self._post,
            request=request,
            tags={
                'app': __name__,
                'authenticated': request.user.is_authenticated,
                'component': 'ResendTokenAPIView._post',
            },
            success_message={
                'detail': UserMessages.USER_CREATED
            },
            success_status=status.HTTP_201_CREATED
        )
    
    def _post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True) 
        
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"message": UserMessages.USER_CREATED}, 
                status=status.HTTP_200_OK
            )
        
        if user.is_active == True:  
            return Response(
                {"error": UserMessages.USER_ALREADY_VERIFIED}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        confirm_url= UsersRegisterService.get_confirmation_url(user, request)                    
        
        ConfirmUserEmail.send_email(
            to_email=user.email, 
            confirm_url=confirm_url, 
            nombre=user.username
        )
        
        self.logger.info(f'Re-enviado email de confirmación a {user.username} - {user.email}')
        
        return Response(
            {"message": UserMessages.VERIFICATION_EMAIL_SENT}, 
            status=status.HTTP_200_OK
        )

@VERIFY_EMAIL
class VerifyEmailAPIView(SentryErrorHandlerMixin, APIView):
    permission_classes = [AllowAny]
    throttle_classes = [SensitiveOperationThrottle]
    serializer_class = VerifyEmailSerializer

    def get(self, request):
        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']

        data = UsersRegisterService.verify_email_token(token)

        if not data:
            return Response(
                {"error": UserMessages.TOKEN_INVALID},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_id = data.get('user_id')
        new_email = data.get('new_email')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": UserMessages.USER_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        # CASO 1: Activación de cuenta
        if not new_email:
            if user.is_active:
                return Response(
                    {"message": UserMessages.USER_ALREADY_VERIFIED},
                    status=status.HTTP_200_OK
                )

            user.is_active = True
            user.save()

            self.logger.info(
                f'Se confirmó el correo de {user.username}, cuenta activada'
            )

            return Response(
                {"message": UserMessages.USER_VERIFIED},
                status=status.HTTP_200_OK
            )

        # CASO 2: Cambio de email
        if User.objects.filter(email=new_email).exclude(id=user_id).exists():
            return Response(
                {"error": UserMessages.EMAIL_NOT_AVAIBLE},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.email = new_email
        user.save()

        self.logger.info(
            f'Se confirmó el correo de {user.username}, nuevo email: {new_email}'
        )

        return Response(
            {"message": UserMessages.NEW_EMAIL},
            status=status.HTTP_200_OK
        )
