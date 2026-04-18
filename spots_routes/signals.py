# spots_routes/signals.py
from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from core.utils.storages import delete_file_fields, delete_if_changed
from .models import RoutePhoto, Spot, SpotCaption
import os
from django.conf import settings

User = get_user_model()

 
#=============================== SIGNALS PARA SPOT =======================================

CAMPOS_SPOT = ['spot_thumbnail_path']

@receiver(pre_save, sender=Spot)
def spot_pre_save(sender, instance, **kwargs):
    """Maneja eliminación de thumbnail antiguo antes de actualizar"""
    if not instance.pk:
        return  # Es un nuevo spot, no hay thumbnail anterior que borrar
    
    try:
        anterior = Spot.objects.get(pk=instance.pk)
    except Spot.DoesNotExist:
        return
    
    # Borra el thumbnail anterior si cambió
    delete_if_changed(anterior, instance, CAMPOS_SPOT)

@receiver(post_delete, sender=Spot)
def spot_post_delete(sender, instance, **kwargs):
    """Borra thumbnail cuando se elimina un Spot"""
    delete_file_fields(instance, CAMPOS_SPOT)


 
#=============================== SIGNALS PARA SPOTCAPTION =======================================

CAMPOS_SPOTCAPTION = ['img_path']

@receiver(pre_save, sender=SpotCaption)
def spotcaption_pre_save(sender, instance, **kwargs):
    """Maneja eliminación de imagen antigua antes de actualizar"""
    if not instance.pk:
        return
    
    try:
        anterior = SpotCaption.objects.get(pk=instance.pk)
    except SpotCaption.DoesNotExist:
        return
    
    delete_if_changed(anterior, instance, CAMPOS_SPOTCAPTION)

@receiver(post_delete, sender=SpotCaption)
def spotcaption_post_delete(sender, instance, **kwargs):
    """Borra imagen cuando se elimina un SpotCaption"""
    delete_file_fields(instance, CAMPOS_SPOTCAPTION)


#=============================== SIGNALS PARA ROUTEPHOTO =======================================

CAMPOS_ROUTEPHOTO = ['img_path']

@receiver(pre_save, sender=RoutePhoto)
def routephoto_pre_save(sender, instance, **kwargs):
    """Maneja eliminación de imagen antigua antes de actualizar"""
    if not instance.pk:
        return
    
    try:
        anterior = RoutePhoto.objects.get(pk=instance.pk)
    except RoutePhoto.DoesNotExist:
        return
    
    delete_if_changed(anterior, instance, CAMPOS_ROUTEPHOTO)

@receiver(post_delete, sender=RoutePhoto)
def routephoto_post_delete(sender, instance, **kwargs):
    """Borra imagen cuando se elimina un RoutePhoto"""
    delete_file_fields(instance, CAMPOS_ROUTEPHOTO)