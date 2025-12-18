import os
from django.contrib.gis.db import models
from django.contrib.gis.db import models as gis_models
from django.core.validators import FileExtensionValidator
from django.utils.html import format_html
from authentication.views import User
from manza_spots.utils import route_photo_path, spot_photo_path, spot_thumbnail_path
from django.contrib.gis.geos import GEOSGeometry

#----------------------------------- SPOTS --------------------------------------------

class SpotStatusReview(models.Model):
    key = models.CharField(max_length=20)
    name = models.TextField()
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.key} - {self.name}"

def get_default_pending():
    """Obtener estado pendiente para utuilizarlo como default en el modelo de spot"""
    return SpotStatusReview.objects.get(key='PENDING').id

def get_approved():
    """Obtener estado aprovado"""
    return SpotStatusReview.objects.get(key='APPROVED').id

def get_rejected():
    """Obtener estado rechazado"""
    return SpotStatusReview.objects.get(key='REJECTED').id

class Spot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='spots_created')
    name = models.CharField(max_length=50)
    description = models.TextField()
    spot_thumbnail_path = models.ImageField(
        upload_to= spot_thumbnail_path ,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
            )
        ],
        help_text="Formatos: JPG, PNG, WEBP"
    )
    location = gis_models.PointField(srid=4326)
    status = models.ForeignKey(SpotStatusReview, on_delete=models.CASCADE, related_name = 'spots', default=get_default_pending)
    reject_reason = models.TextField(null=True, blank=True)
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='spots_reviewed', blank=True, null=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name}"
    
    def delete(self, *args, **kwargs):
        """Eliminar thumbnail al borrar el spot"""
        if self.spot_thumbnail_path:
            try:
                if os.path.isfile(self.spot_thumbnail_path.path):
                    os.remove(self.spot_thumbnail_path.path)
            except (ValueError, AttributeError):
                pass
        super().delete(*args, **kwargs)
    
    def save(self, *args, **kwargs):
        """Eliminar thumbnail anterior si se cambia"""
        if self.pk:  # Si ya existe
            try:
                old = Spot.objects.get(pk=self.pk)
                if old.spot_thumbnail_path and old.spot_thumbnail_path != self.spot_thumbnail_path:
                    if os.path.isfile(old.spot_thumbnail_path.path):
                        os.remove(old.spot_thumbnail_path.path)
            except Spot.DoesNotExist:
                pass
        super().save(*args, **kwargs)
    
class SpotCaption(models.Model):
    spot = models.ForeignKey(Spot, on_delete=models.CASCADE, related_name='captions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='captions_made')
    description = models.TextField(blank=True, null=True)
    img_path = models.ImageField(
        upload_to=spot_photo_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
            )
        ],
        help_text="Formatos: JPG, PNG, WEBP"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"photo spot: {self.spot} for user: {self.user}"
    
    def delete(self, *args, **kwargs):
        """Eliminar archivo físico al borrar el registro"""
        if self.img_path:  # ← CAMBIO AQUÍ: era self.image
            try:
                if os.path.isfile(self.img_path.path):
                    os.remove(self.img_path.path)
            except (ValueError, AttributeError):
                pass
        super().delete(*args, **kwargs)
    
class UserFavoriteSpot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_spots')
    spot = models.ForeignKey(Spot, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null = True)
    deleted_at = models.DateTimeField(blank=True, null = True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"favorite spot:{self.spot} user: {self.user}"
    

#----------------------- ROUTES -------------------------------------

class Difficulty(models.Model):
    name = models.CharField(max_length=50) #Facil, Intermedio, Dificil
    key = models.CharField(max_length=10)
    hex_color = models.CharField(max_length=7)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name}"
    
class TravelMode(models.Model):
    name = models.CharField(max_length=50)
    key = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name}"
    
class Route(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routes_created')
    spot = models.ForeignKey(Spot, on_delete=models.CASCADE, related_name='routes')
    difficulty = models.ForeignKey(Difficulty, on_delete=models.CASCADE, related_name='routes_with_dificulty')
    travel_mode = models.ForeignKey(TravelMode, on_delete=models.CASCADE, related_name = 'routes_with_mode')
    description = models.TextField(blank=True, null=True)
    distance = models.DecimalField(max_digits=10, decimal_places=2, editable=False) 
    path = gis_models.LineStringField(geography=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"route id: {self.pk} - spot: {self.spot}"
    

    def save(self, *args, **kwargs):
        """
        Calculamos la distancia en KM usando un SRID en metros
        """
        if self.path:
            path_m = self.path.transform(3857, clone=True)
            distance_meters = path_m.length
            self.distance = round(distance_meters / 1000, 2)
        else:
            self.distance = 0

        super().save(*args, **kwargs)

    
class RoutePhoto(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='photo')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photo_by')
    img_path = models.ImageField(
        upload_to=route_photo_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
            )
        ],
        help_text="Formatos: JPG, PNG, WEBP"
    )
    location = gis_models.PointField(srid=4326, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"photo id: {self.pk} - ruta: {self.route}"
    
    def delete(self, *args, **kwargs):
        """Eliminar archivo físico al borrar el registro"""
        if self.img_path:  
            try:
                if os.path.isfile(self.img_path.path):
                    os.remove(self.img_path.path)
            except (ValueError, AttributeError):
                pass
        super().delete(*args, **kwargs)

class UserFavoriteRoute(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_routes')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'route')  
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
        
    def __str__(self):
        return f"favorite route: {self.pk} - route: {self.route}"