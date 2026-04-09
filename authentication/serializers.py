# serializers.py
import re
from rest_framework import serializers
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from dj_rest_auth.registration.serializers import SocialLoginSerializer

from core.responses.messages import AuthMessages

User = get_user_model()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class SetNewPasswordSerializer(serializers.Serializer):
    uidb64        = serializers.CharField()
    token         = serializers.CharField()
    new_password  = serializers.CharField(min_length=6, write_only=True, trim_whitespace=False)
    confirm_new_password = serializers.CharField(min_length=6, write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError(
                {'confirm_new_password': AuthMessages.PASSWORD_MISMATCH}
            )
        return attrs

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer que permite autenticación con username o email"""
    
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        if not username and not email:
            raise serializers.ValidationError({
                'non_field_errors': ['Debe proporcionar username o email']
            })

        if username and email:
            raise serializers.ValidationError({
                'non_field_errors': ['Proporcione solo username o email, no ambos']
            })

        if email:
            try:
                user = User.objects.get(email=email)
                attrs['username'] = user.username  
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    'email': ['Usuario no encontrado con este email']
                })

        return super().validate(attrs)
class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para creación de usuarios con contraseña"""
    password = serializers.CharField(
        write_only=True, required=True,
        validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'email']
        extra_kwargs = {
            'email': {'required': True}
        }

    def validate_username(self, value):
        value = value.strip()  

        if len(value) < 5:
            raise serializers.ValidationError(
                "El nombre de usuario debe tener al menos 5 caracteres."
            )
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError(
                "El nombre de usuario solo puede contener letras, números, _ y -"
            )
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "Este nombre de usuario ya está en uso."
            )

        return value
    
    def validate(self, attrs):
        attrs['email'] = attrs['email'].lower().strip()

        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                "password": "Las contraseñas no coinciden."
            })
        if User.objects.filter(email__iexact=attrs['email']).exists():
            raise serializers.ValidationError({
                "email": "Este email ya está registrado."
            })
        return attrs
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user
    
class ResendTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField(
        required=True,
        max_length=512,
        trim_whitespace=True
    )

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError(
                {"confirm_new_password": "Las contraseñas nuevas no coinciden."}
            )
        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError(
                {"new_password": "La nueva contraseña debe ser diferente a la actual."}
            )
        return attrs
    

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=False,
        allow_blank=False,
        trim_whitespace=True,
    )
    email = serializers.EmailField(
        required=False,
        allow_blank=False,
        trim_whitespace=True,
    )
    password = serializers.CharField(
        required=False,        
        write_only=True,
        style={'input_type': 'password'},
        trim_whitespace=False,  
    )

    def validate_email(self, value):
        return value.lower()

    def validate_username(self, value):
        return value.lower()

    def validate(self, attrs):
        password = attrs.get('password')
        username = attrs.get('username')
        email    = attrs.get('email')

        if not password:
            raise serializers.ValidationError(
                AuthMessages.PASSWORD_REQUIRED
            )

        if not username and not email:
            raise serializers.ValidationError(
                AuthMessages.EMAIL_OR_USERNAME_REQUIRED
            )

        return attrs
    

class GoogleIDTokenSerializer(SocialLoginSerializer):
    id_token = serializers.CharField(required=True)
    access_token = serializers.CharField(required=False, allow_blank=True)
    code = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        id_token_value = attrs.get('id_token')
        if not id_token_value:
            raise serializers.ValidationError({'id_token': 'Este campo es requerido.'})
        
        attrs['access_token'] = id_token_value
        
        return super().validate(attrs)