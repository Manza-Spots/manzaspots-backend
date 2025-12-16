# myapp/utils.py
import os
from datetime import datetime
from uuid import uuid4

def upload_image_path(base_folder, instance, filename, use_spot=False, use_route=False):
    """
    Función genérica para generar rutas de upload de imágenes.
    
    Args:
        base_folder: Carpeta base ('spots', 'routes', etc.)
        instance: Instancia del modelo
        filename: Nombre original del archivo (solo usamos la extensión)
        use_spot: Si True, incluye spot_{id} en la ruta
        use_route: Si True, incluye route_{id} en la ruta
    
    Returns:
        String con la ruta completa
    """
    # Obtener solo la extensión del archivo original
    ext = filename.split('.')[-1].lower()
    
    # Validar extensión (seguridad adicional)
    allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']
    if ext not in allowed_extensions:
        ext = 'jpg'  # Default fallback
    
    # Obtener fecha actual
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    
    # Generar nombre único y descriptivo
    # Formato: userid_timestamp_uuid.ext
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid4())[:8]  # Primeros 8 caracteres del UUID
    new_filename = f"{instance.user.id}_{timestamp}_{unique_id}.{ext}"
    
    # Construir la ruta según los parámetros
    path_parts = [base_folder]
    
    if use_spot and hasattr(instance, 'spot'):
        path_parts.append(f'spot_{instance.spot.id}')
    
    if use_route and hasattr(instance, 'route'):
        path_parts.append(f'route_{instance.route.id}')
    
    # Agregar año/mes
    path_parts.extend([year, month])
    
    # Agregar nombre de archivo
    path_parts.append(new_filename)
    
    return os.path.join(*path_parts)


# Funciones wrapper específicas para cada tipo
def spot_photo_path(instance, filename):
    """
    Ruta para fotos de spots
    Resultado: spots/spot_123/2025/01/5_20250115_143022_a1b2c3d4.jpg
    """
    return upload_image_path('spots', instance, filename, use_spot=True)


def route_photo_path(instance, filename):
    """
    Ruta para fotos de rutas
    Resultado: routes/spot_123/route_456/2025/01/5_20250115_143022_a1b2c3d4.jpg
    """
    return upload_image_path('routes', instance, filename, use_spot=True, use_route=True)

def spot_thumbnail_path(instance, filename):
    """
    Ruta para la miniatura del spot
    Resultado: spot_thumbnails/spot_1.jpg
    """
    ext = filename.split('.')[-1].lower()
    
    # Validar extensión
    allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']
    if ext not in allowed_extensions:
        ext = 'jpg'
    
    # Si es nuevo (aún no tiene ID), usar timestamp temporal
    if instance.pk is None:
        from datetime import datetime
        temp_name = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return f'spot_thumbnails/{temp_name}.{ext}'
    
    # Si ya existe, usar el ID del spot
    return f'spot_thumbnails/spot_{instance.pk}.{ext}'
