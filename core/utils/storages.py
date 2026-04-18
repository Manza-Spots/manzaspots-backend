def delete_storage_file(field):
    """Funciona con cualquier backend: local, S3, R2, etc."""
    if field and field.name:
        if field.storage.exists(field.name):
            field.storage.delete(field.name)

def file_field_changed(previous, new_instance, field_name: str) -> bool:
    previous_field = getattr(previous, field_name)
    new_field = getattr(new_instance, field_name)
    new_name = new_field.name if new_field else None
    return bool(
        previous_field
        and previous_field.name
        and previous_field.name != new_name
    )

def delete_file_fields(instance, fields: list[str]):
    """Borra una lista de campos de archivo de una instancia."""
    for field in fields:
        delete_storage_file(getattr(instance, field))

def delete_if_changed(previous, new_instance, fields: list[str]):
    """Borra archivos antiguos solo si el campo cambió."""
    for field in fields:
        if file_field_changed(previous, new_instance, field):
            delete_storage_file(getattr(previous, field))