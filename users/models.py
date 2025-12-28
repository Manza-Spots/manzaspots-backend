from django.db import models
from django.core.validators import FileExtensionValidator
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.db.models import DecimalField, Sum, Value
from authentication.views import User
from manza_spots.utils import user_thumbnail_path
from spots_routes.models import Route, Spot

class UserProfile(models.Model):
    user = models.OneToOneField(User, verbose_name=("usuario id"), on_delete=models.CASCADE, related_name='profile')
    profile_thum_path = models.ImageField(
        upload_to= user_thumbnail_path ,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
            )
        ],
        help_text="Formatos: JPG, PNG, WEBP",
        blank=True, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def routes_created(self) -> int:
        return Route.objects.filter(user = self.user, is_active=True).count()
    
    def spots_created(self) -> int:
        return Spot.objects.filter(user = self.user, is_active=True).count()    
       
    def distance_traveled_km(self) -> Decimal:
        return (
            Route.objects
            .filter(user=self.user, is_active=True)
            .aggregate(
                total=Coalesce(
                    Sum('distance'),
                    Value(0),
                    output_field=DecimalField(                    
                        max_digits=10,
                        decimal_places=2
                    )
                )
            )['total']
        )
    
    