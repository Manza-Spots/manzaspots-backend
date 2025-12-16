from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SpotStatusReview, Spot, SpotCaption, UserFavoriteSpot,
    Difficulty, TravelMode, Route, RoutePhoto, UserFavoriteRoute
)

# -------------------- SPOTS -----------------------------

@admin.register(SpotStatusReview)
class SpotStatusReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "key", "name", "is_active")
    search_fields = ("key", "name")
    list_filter = ("is_active",)


class SpotCaptionInline(admin.TabularInline):
    model = SpotCaption
    extra = 0
    readonly_fields = ("created_at",)


@admin.action(description="Marcar Spots como activos")
def activar_spots(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.action(description="Marcar Spots como inactivos")
def desactivar_spots(modeladmin, request, queryset):
    queryset.update(is_active=False)


from django.contrib.gis import admin as gis_admin

@admin.register(Spot)
class SpotAdmin(gis_admin.GISModelAdmin):
    gis_widget_kwargs = {
        'attrs': {
            'default_zoom': 12,
            'default_lat': 19.0519,
            'default_lon': -104.3186,
        },
    }
    
    list_display = (
        "id",
        "thumbnail_preview",
        "name",
        "user",
        "status",
        "is_active",
        "created_at",
        "location_display",
    )
    search_fields = ("name", "description", "user__username")
    list_filter = ("status", "is_active", "created_at")
    readonly_fields = ("created_at", "reviewed_at", "thumbnail_preview")
    inlines = [SpotCaptionInline]
    actions = [activar_spots, desactivar_spots]

    def thumbnail_preview(self, obj):
        """Muestra la miniatura del Spot en el admin."""
        if obj.spot_thumbnail_path:
            try:
                return format_html(
                    '<img src="{}" width="70" height="70" style="border-radius:5px; object-fit:cover;" />',
                    obj.spot_thumbnail_path.url
                )
            except ValueError:
                # En caso de que el archivo no exista físicamente
                return format_html('<span style="color:red;">Imagen no encontrada</span>')
        return format_html('<span style="color:gray;">Sin imagen</span>')
    
    thumbnail_preview.short_description = "Thumbnail"

    def location_display(self, obj):
        if not obj.location:
            return "-"
        return f"{obj.location.y:.6f}, {obj.location.x:.6f}"
    
    location_display.short_description = "Coordenadas"


@admin.register(SpotCaption)
class SpotCaptionAdmin(admin.ModelAdmin):
    list_display = ("id", "spot", "user", "img_path", "is_active", "created_at")
    search_fields = ("img_path", "spot__name", "user__username")
    list_filter = ("is_active", "created_at")


@admin.register(UserFavoriteSpot)
class UserFavoriteSpotAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "spot", "is_active", "created_at")
    search_fields = ("user__username", "spot__name")
    list_filter = ("is_active",)


# -------------------- ROUTES -----------------------------

@admin.register(Difficulty)
class DifficultyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "key", "hex_color", "is_active")
    search_fields = ("name", "key")
    list_filter = ("is_active",)


@admin.register(TravelMode)
class TravelModeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "key", "is_active")
    search_fields = ("name", "key")
    list_filter = ("is_active",)


class RoutePhotoInline(admin.TabularInline):
    model = RoutePhoto
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "spot",
        "difficulty",
        "travel_mode",
        "distance",
        "is_active",
        "created_at",
    )
    search_fields = ("user__username", "spot__name")
    list_filter = ("difficulty", "travel_mode", "is_active")
    readonly_fields = ("created_at", "updated_at")
    inlines = [RoutePhotoInline]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("user", "spot", "difficulty", "travel_mode")
        )


@admin.register(RoutePhoto)
class RoutePhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "route", "user", "image_preview", "is_active", "created_at")
    search_fields = ("route__id", "user__username")
    list_filter = ("is_active",)
    readonly_fields = ("image_preview_large",)
    
    def image_preview(self, obj):
        """Thumbnail pequeño para la lista"""
        if obj.img_path:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.img_path.url
            )
        return "Sin imagen"
    image_preview.short_description = "Vista previa"
    
    def image_preview_large(self, obj):
        """Imagen grande para el detalle"""
        if obj.img_path:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 400px; border-radius: 8px;" />',
                obj.img_path.url
            )
        return "Sin imagen"
    image_preview_large.short_description = "Imagen"


@admin.register(UserFavoriteRoute)
class UserFavoriteRouteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "route", "spot", "is_active", "created_at")
    search_fields = ("user__username", "route__id", "spot__name")
    list_filter = ("is_active",)
