from rest_framework import serializers
from spots_routes.models import Spot, SpotCaption, UserFavoriteSpot


class SpotCaptionSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = SpotCaption
        fields = ['description', 'img_path', 'created_at', 'user', 'user_name', 'spot']
        read_only_fields = ['user', 'created_at']  


    def get_user_name(self, obj):
        return obj.user.username
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class SpotCaptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpotCaption
        fields = ['spot', 'img_path', 'description']
    
    def validate_spot(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Este spot esta inacvtivo")
        return value
    
class SpotSerializer(serializers.ModelSerializer):
    spot_caption = SpotCaptionSerializer(many=True, read_only=True, source='captions')
    is_favorite = serializers.SerializerMethodField() #ojito eh, el serializerMehotField busco un metodo dentro de esta clase para ejecutarlo y guardar la info como un serializer ,as para ello debe tener el mismo nombre que cabron
    user_name = serializers.CharField(source='user.username', read_only=True)
    status_name = serializers.CharField(source = 'status.name')
    class Meta:
        model = Spot
        fields = [
            # Campos básicos del modelo
            'id',
            'name',
            'description',
            'spot_thumbnail_path',
            'location',
            'user',
            'user_name',
            'created_at',
            
            # Campos de estado (solo para admins - se eliminarán en __init__)
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
    
    def get_is_favorite(self, obj):
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
                'status', 'reject_reason', 'reviewed_user', 
                'reviewed_at', 'deleted_at'
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