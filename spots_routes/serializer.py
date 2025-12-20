from rest_framework import serializers
from spots_routes.models import Difficulty, Route, RoutePhoto, Spot, SpotCaption, TravelMode, UserFavoriteRoute, UserFavoriteSpot
from rest_framework_gis.fields import GeometryField
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

class SpotCaptionSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = SpotCaption
        fields = ['id','description', 'img_path', 'created_at', 'user', 'user_name', 'spot']
        read_only_fields = ['user', 'created_at']  


    def get_user_name(self, obj) -> str:
        return obj.user.username
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class SpotCaptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpotCaption
        fields = ['img_path', 'description']
    
    def validate_spot(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Este spot esta inacvtivo")
        return value
    
class SpotSerializer(serializers.ModelSerializer):
    spot_caption = SpotCaptionSerializer(many=True, read_only=True, source='photos')  
    is_favorite = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.username', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)
    location = GeometryField() 
    class Meta:
        model = Spot
        fields = [
            # Campos básicos del modelo
            'id',
            'name',
            'description',
            'spot_thumbnail_path',  
            'location',
            'user_name',
            'created_at',
            
            # Campos de estado (solo para admins)
            'status_name', 
            'reject_reason',
            'reviewed_user',
            'reviewed_at',
            'deleted_at',
            'is_active',
            
            # Campos anidados
            'spot_caption',
            'is_favorite',
        ]
        
        read_only_fields = ['user', 'created_at']
    
    def get_is_favorite(self, obj) -> bool:
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserFavoriteSpot.objects.filter(
                user=request.user,
                spot=obj,
                is_active=True
            ).exists()
        return False
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        
        if request and hasattr(request, 'user'):
            user = request.user
            
            # Campos que solo admins pueden ver
            admin_fields = {
                'status_name',  # ✅ Agregado aquí también
                'reject_reason', 
                'reviewed_user', 
                'reviewed_at', 
                'deleted_at'
            }
            
            if not user.is_staff:
                # Remover campos de admin
                for field in admin_fields:
                    self.fields.pop(field, None)

class UserFavoriteSpotSerializer(serializers.ModelSerializer):
    spot = SpotSerializer(read_only=True)
    
    class Meta:
        model = UserFavoriteSpot
        fields = ['id', 'spot', 'created_at', 'is_active']


#=================================== SPOTS =========================================================
        
class RoutePhotoSerializer(serializers.ModelSerializer):
    location = GeometryField() 
    user_name = serializers.CharField(
        source='user.username',
        read_only=True
    )
    
    class Meta:
        model = RoutePhoto 
        fields = ['id', 'user', 'user_name', 'route', 'img_path', 'location', 'created_at'] 
        read_only_fields = ['id', 'user', 'created_at']

class RoutePhotoCreateSerializer(serializers.ModelSerializer):
    location = GeometryField() 
    class Meta: 
        model = RoutePhoto
        fields = ['img_path', 'location']
    
class RouteSerializer(serializers.ModelSerializer):
    route_photos = RoutePhotoSerializer(many=True, read_only=True, source='photo')  
    user_name = serializers.CharField(source='user.username', read_only=True)
    difficulty_name = serializers.CharField(source='difficulty.name', read_only=True)
    travel_mode_name = serializers.CharField(source='travel_mode.name', read_only=True)
    is_favorite = serializers.SerializerMethodField()
    travel_mode = serializers.SlugRelatedField(
        slug_field = "key",
        queryset = TravelMode.objects.all()
    )
    difficulty = serializers.SlugRelatedField(
        slug_field = "key",
        queryset = Difficulty.objects.all()
    )
    
    class Meta:
        path = GeometryField() 
        model = Route
        fields = [
            'id', 'user', 'user_name', 'difficulty', 'difficulty_name',
            'travel_mode', 'travel_mode_name', 'description', 
            'path', 'is_active', 'route_photos', 'is_favorite', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'distance','spot']
    
    def get_is_favorite(self, obj) -> bool:
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserFavoriteRoute.objects.filter(
                user=request.user,
                route=obj,  
                is_active=True
            ).exists()
        return False

class UserFavoriteRouteSerializer(serializers.ModelSerializer):
    route = RouteSerializer(read_only=True)
    
    class Meta:
        model = UserFavoriteRoute
        fields = ['id', 'route', 'created_at', 'is_active']
