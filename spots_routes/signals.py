# spots_routes/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import RoutePhoto, Spot, SpotCaption
import os
from django.conf import settings
import os
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.gis.db import models
from django.contrib.gis.db import models as gis_models
from django.core.validators import FileExtensionValidator
from authentication.views import User

@receiver(post_save, sender=Spot)
def rename_thumbnail_after_create(sender, instance, created, **kwargs):
    """Renombrar thumbnail después de crear el spot"""
    if created and instance.spot_thumbnail_path:
        old_path = instance.spot_thumbnail_path.path
        
        # Si el nombre contiene 'temp_', renombrarlo
        if 'temp_' in os.path.basename(old_path):
            ext = old_path.split('.')[-1]
            new_filename = f'spot_{instance.pk}.{ext}'
            new_path = os.path.join(
                os.path.dirname(old_path),
                new_filename
            )
            
            # Renombrar archivo físico
            if os.path.isfile(old_path):
                os.rename(old_path, new_path)
                
                # Actualizar el campo en la BD
                instance.spot_thumbnail_path.name = f'spot_thumbnails/{new_filename}'
                # Usar update() para evitar loop infinito con save()
                Spot.objects.filter(pk=instance.pk).update(
                    spot_thumbnail_path=instance.spot_thumbnail_path.name
                )

@receiver(pre_delete, sender=Spot)
def delete_spot_thumbnail(sender, instance, **kwargs):
    """Eliminar thumbnail cuando se borra un Spot"""
    if instance.spot_thumbnail_path:
        try:
            if os.path.isfile(instance.spot_thumbnail_path.path):
                os.remove(instance.spot_thumbnail_path.path)
        except (ValueError, AttributeError, FileNotFoundError):
            pass

@receiver(pre_save, sender=Spot)
def delete_old_spot_thumbnail_on_update(sender, instance, **kwargs):
    """Eliminar thumbnail anterior cuando se actualiza"""
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.spot_thumbnail_path and old_instance.spot_thumbnail_path != instance.spot_thumbnail_path:
                if os.path.isfile(old_instance.spot_thumbnail_path.path):
                    os.remove(old_instance.spot_thumbnail_path.path)
        except sender.DoesNotExist:
            pass
        except (ValueError, AttributeError, FileNotFoundError):
            pass

@receiver(pre_delete, sender=SpotCaption)
def delete_spot_caption_image(sender, instance, **kwargs):
    """Eliminar imagen cuando se borra un SpotCaption"""
    if instance.img_path:
        try:
            if os.path.isfile(instance.img_path.path):
                os.remove(instance.img_path.path)
        except (ValueError, AttributeError, FileNotFoundError):
            pass

@receiver(pre_delete,sender=RoutePhoto)
def delete_route_photo_image(sender, instance, **kwargs):
    """Eliminar imagen cuando se borra un RoutePhoto"""
    if instance.img_path:
        try:
            if os.path.isfile(instance.img_path.path):
                os.remove(instance.img_path.path)
        except (ValueError, AttributeError, FileNotFoundError):
            pass