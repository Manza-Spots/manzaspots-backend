from django.db import migrations

DIFFICULTIES = [
    {'key': 'EASY', 'name': 'Fácil', 'hex_color': '#2E9E5B'},
    {'key': 'MEDIUM', 'name': 'Intermedio', 'hex_color': '#E0A325'},
    {'key': 'HARD', 'name': 'Difícil', 'hex_color': '#D9544D'},
]

TRAVEL_MODES = [
    {'key': 'WALKING', 'name': 'A pie'},
    {'key': 'CYCLING', 'name': 'Bicicleta'},
    {'key': 'DRIVING', 'name': 'Automóvil'},
]


def seed_catalogs(apps, schema_editor):
    """Crea los catálogos base solo si están vacíos (sin pisar datos de producción)."""
    Difficulty = apps.get_model('spots_routes', 'Difficulty')
    TravelMode = apps.get_model('spots_routes', 'TravelMode')

    if not Difficulty.objects.exists():
        Difficulty.objects.bulk_create([Difficulty(**data) for data in DIFFICULTIES])

    if not TravelMode.objects.exists():
        TravelMode.objects.bulk_create([TravelMode(**data) for data in TRAVEL_MODES])


def reverse_func(apps, schema_editor):
    Difficulty = apps.get_model('spots_routes', 'Difficulty')
    TravelMode = apps.get_model('spots_routes', 'TravelMode')
    Difficulty.objects.filter(key__in=[d['key'] for d in DIFFICULTIES]).delete()
    TravelMode.objects.filter(key__in=[t['key'] for t in TRAVEL_MODES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('spots_routes', '0006_spot_storage_id'),
    ]
    operations = [
        migrations.RunPython(seed_catalogs, reverse_func),
    ]
