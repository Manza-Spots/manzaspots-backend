
from authentication import serializers
from spots_routes.models import Spot, SpotCaption, UserFavoriteSpot


class UserFavoriteSpotSerializer(serializers.ModelSerializer):
    class Meta:
        model=UserFavoriteSpot
        fields = []
        
class SpotCaptionSerializer(serializers.ModelSerializer):
    class Meta:
        model=SpotCaption
        fields = []
        

class SpotSerializer(serializers.ModelSerializer):
    class Meta:
        model=Spot
        fields = [all]
        read_only_fields = ['is_active', 'deleted_at', 'created_at', 'reviewed_at', 'reviewed_user']