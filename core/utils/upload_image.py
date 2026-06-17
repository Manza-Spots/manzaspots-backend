# myapp/utils.py
import os
from datetime import datetime
from uuid import uuid4

def generate_upload_path(base_folder, instance, filename, purpose='general', owner_field=None):
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    if ext not in ('jpg', 'jpeg', 'png', 'webp', 'mp4', 'mov'):
        ext = 'jpg'

    if owner_field:
        owner = getattr(instance, owner_field)
        owner_id = owner.pk
    else:
        owner_id = instance.storage_id  
    unique_name = uuid4().hex[:12]
    return f"{base_folder}/{owner_id}/{purpose}/{unique_name}.{ext}"


def upload_spot_photo(instance, filename):
    """
    Ruta para fotos de spots
    Resultado: Spots/{spot_storage_id}/Photos/{unique_name}.ext
    """
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    if ext not in ('jpg', 'jpeg', 'png', 'webp', 'mp4', 'mov'):
        ext = 'jpg'
    unique_name = uuid4().hex[:12]
    spot_uuid = instance.spot.storage_id  
    return f"Spots/{spot_uuid}/Photos/{unique_name}.{ext}"

def upload_route_photo(instance, filename):
    """
    Ruta para fotos de rutas
    Resultado: Spots/{spot_storage_id}/Routes/{unique_name}.ext
    """
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    if ext not in ('jpg', 'jpeg', 'png', 'webp', 'mp4', 'mov'):
        ext = 'jpg'
    unique_name = uuid4().hex[:12]
    spot_uuid = instance.route.spot.storage_id  
    return f"Spots/{spot_uuid}/Routes/{unique_name}.{ext}"


def upload_spot_thumbnail(instance, filename):
    """
    Ruta para la miniatura del spot
    Resultado: spots/spot_id/Thumbnail/uuid
    """
    return generate_upload_path('Spots', instance, filename, purpose='Thumbnail')

def upload_user_thumbnail(instance, filename):
    """
    Ruta para la foto de perfil del usuario
    Resultado: Users/user_id/Thumbnail/uuid
    """
    return generate_upload_path('User', instance, filename, purpose='Thumbnail', owner_field='user')

