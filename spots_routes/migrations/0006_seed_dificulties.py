from django.db import migrations


def seed_all(apps, schema_editor):
    Difficulty = apps.get_model("spots_routes", "Difficulty")
    TravelMode = apps.get_model("spots_routes", "TravelMode")

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

    modes = [
        ("Caminando", "walking"),
        ("Bicicleta", "cycling"),
    ]

    for name, key in modes:
        TravelMode.objects.update_or_create(
            key=key,
            defaults={
                "name": name,
                "is_active": True,
            }
        )


def reverse_seed(apps, schema_editor):
    Difficulty = apps.get_model("spots_routes", "Difficulty")
    TravelMode = apps.get_model("spots_routes", "TravelMode")

    Difficulty.objects.filter(
        key__in=["easy", "medium", "hard"]
    ).delete()

    TravelMode.objects.filter(
        key__in=["walking", "cycling"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("spots_routes", "0005_remove_spotcaption_caption_routephoto_coords_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_all, reverse_seed),
    ]
