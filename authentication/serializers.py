# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

User = get_user_model()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class SetNewPasswordSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=6, write_only=True)

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
