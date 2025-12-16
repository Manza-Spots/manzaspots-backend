from django.db import models

from authentication.views import User

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, verbose_name=("usuario id"), on_delete=models.CASCADE, related_name='profile')
    profile_thum_path = models.CharField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    routes_created = models.IntegerField(default=0)
    spot_created = models.IntegerField(default=0)
    distance_traveled_km = models.IntegerField(null=True, blank=True)
    
    