from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from users.models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    distance_traveled_km = serializers.SerializerMethodField()
    routes_created = serializers.SerializerMethodField()
    spots_created = serializers.SerializerMethodField()
    class Meta: 
        model = UserProfile
    class Meta:
        model = UserProfile
        fields = [
            'user',
            'profile_thum_path',
            'distance_traveled_km',
            'routes_created',
            'spots_created',
        ]
        read_only_fields = [
            'distance_traveled_km',
            'routes_created',
            'spots_created',
        ]
    
    def get_distance_traveled_km(self, obj):
        return obj.distance_traveled_km()
    
    def get_routes_created(self, obj):
        return obj.routes_create()
    
    def get_spots_created(self, obj):
        return obj.spot_create()
    
class UserProfileThumbSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['profile_thum_path']
        
class UserSerializer(serializers.ModelSerializer):
    """Serializer para lectura de usuarios"""
    profile = UserProfileSerializer()
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'is_active', 'date_joined', 'last_login', 'profile']
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para creación de usuarios con contraseña"""
    password = serializers.CharField(
        write_only=True, required=True, 
        validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email']
        extra_kwargs = {
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Las contraseñas no coinciden."
            })
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({
                "email": "Este email ya está registrado."
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    
    """Serializer para actualización de usuarios"""
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']
        extra_kwargs = {
            'username': {'required': False}
        }
    

