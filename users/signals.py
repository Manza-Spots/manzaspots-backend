from django.db.models.signals import post_delete, post_save, pre_save  
from django.dispatch import receiver 
from django.contrib.auth import get_user_model

from core.utils.storages import delete_file_fields, delete_if_changed
User = get_user_model()  
from .models import UserProfile

CAMPOS_USERPROFILE = ['profile_thum_path']

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """
    Esta función se ejecuta automáticamente cada vez que se guarda un User.
    """
    
    if created:  
        UserProfile.objects.create(user=instance)
        print(f"Perfil creado para {instance.username}")



@receiver(pre_save, sender=UserProfile)
def userprofile_pre_save(sender, instance, **kwargs):
    """Maneja eliminación de thumbnail antiguo antes de actualizar"""
    if not instance.pk:
        return  
    
    try:
        anterior = UserProfile.objects.get(pk=instance.pk)
    except UserProfile.DoesNotExist:
        return
    
    
    delete_if_changed(anterior, instance, CAMPOS_USERPROFILE)

@receiver(post_delete, sender=UserProfile)
def userprofile_post_delete(sender, instance, **kwargs):
    """Borra thumbnail cuando se elimina un UserProfile"""
    delete_file_fields(instance, CAMPOS_USERPROFILE)