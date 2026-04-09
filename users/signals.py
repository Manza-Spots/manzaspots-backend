from django.db.models.signals import post_save  
from django.dispatch import receiver 
from django.contrib.auth import get_user_model
User = get_user_model()  
from .models import UserProfile

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """
    Esta función se ejecuta automáticamente cada vez que se guarda un User.
    """
    
    if created:  
        UserProfile.objects.create(user=instance)
        print(f"Perfil creado para {instance.username}")
