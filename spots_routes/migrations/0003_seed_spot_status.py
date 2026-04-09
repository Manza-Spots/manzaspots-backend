# spots_routes/migrations/0002_seed_spot_status.py
from django.db import migrations

def create_default_statuses(apps, schema_editor):
    SpotStatusReview = apps.get_model('spots_routes', 'SpotStatusReview')
    statuses = [
        {'key': 'PENDING', 'name': 'Pendiente de revisión', 'is_active': True},
        {'key': 'APPROVED', 'name': 'Aprobado', 'is_active': True},
        {'key': 'REJECTED', 'name': 'Rechazado', 'is_active': True},
    ]
    for status_data in statuses:
        SpotStatusReview.objects.get_or_create(
            key=status_data['key'],
            defaults={
                'name': status_data['name'],
                'is_active': status_data['is_active']
            }
        )

def reverse_func(apps, schema_editor):
    SpotStatusReview = apps.get_model('spots_routes', 'SpotStatusReview')
    SpotStatusReview.objects.filter(key__in=['PENDING', 'APPROVED', 'REJECTED']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('spots_routes', '0002_initial'),
    ]
    operations = [
        migrations.RunPython(create_default_statuses, reverse_func),
    ]