from django.db import migrations


def seed_difficulties(apps, schema_editor):
    Difficulty = apps.get_model("spots_routes", "Difficulty")

    difficulties = [
        ("Fácil", "easy", "#4CAF50"),
        ("Intermedio", "medium", "#FFC107"),
        ("Difícil", "hard", "#F44336"),
    ]

    for name, key, color in difficulties:
        Difficulty.objects.update_or_create(
            key=key,
            defaults={
                "name": name,
                "hex_color": color,
                "is_active": True,
            }
        )


def reverse_seed(apps, schema_editor):
    Difficulty = apps.get_model("spots_routes", "Difficulty")
    Difficulty.objects.filter(key__in=["easy", "medium", "hard"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('spots_routes', '0005_remove_spotcaption_caption_routephoto_coords_and_more'),
    ]
    
    operations = [
        migrations.RunPython(seed_difficulties, reverse_seed),
    ]

