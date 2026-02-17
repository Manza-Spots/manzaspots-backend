from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from decimal import Decimal
from django.contrib.auth.hashers import check_password

from users.models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    distance_traveled_km = serializers.SerializerMethodField()
    routes_created = serializers.SerializerMethodField()
    spots_created = serializers.SerializerMethodField()
    class Meta:
        model = UserProfile
        fields = [
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
    
    def get_distance_traveled_km(self, obj) -> Decimal:
        return obj.distance_traveled_km()
    
    def get_routes_created(self, obj) -> int:
        return obj.routes_created()
    
    def get_spots_created(self, obj) -> int:
        return obj.spots_created()
    
class UserProfileThumbSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['profile_thum_path']
        
class UserAdminSerializer(serializers.ModelSerializer):
    """Serializer para lectura de usuarios"""
    profile = UserProfileSerializer()
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'is_active', 'date_joined', 'last_login', 'profile']
        read_only_fields = ['id', 'date_joined', 'last_login']

class UserPublicSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    class Meta:
        model = User
        fields = ['username','first_name', 'last_name', 'profile']
class UserPrivateSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    class Meta:
        model = User
        fields = [ 'username', 'email', 'first_name', 'last_name',  'profile']
        read_only_fields = ['email']

class UserUpdateSerializer(serializers.ModelSerializer):
    
    """Serializer para actualización de usuarios"""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']
        extra_kwargs = {
            'username': {'required': False}
        }

class EmailUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        """Valida que la contraseña sea correcta"""
        user = self.context['request'].user
        
        if not check_password(data['password'], user.password):
            raise serializers.ValidationError({
                'password': 'Contraseña incorrecta.'
            })
        
        return data

