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


@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "user",
        "status",
        "is_active",
        "created_at",
        "location_display",
    )
    search_fields = ("name", "description", "user__username")
    list_filter = ("status", "is_active", "created_at")
    readonly_fields = ("created_at", "reviewed_at")
    inlines = [SpotCaptionInline]
    actions = [activar_spots, desactivar_spots]

    def location_display(self, obj):
        if not obj.location:
            return "-"
        return f"{obj.location.y:.5f}, {obj.location.x:.5f}"
    location_display.short_description = "Coords"

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("user", "status", "reviewed_user")
        )


@admin.register(SpotCaption)
class SpotCaptionAdmin(admin.ModelAdmin):
    list_display = ("id", "spot", "user", "caption", "is_active", "created_at")
    search_fields = ("caption", "spot__name", "user__username")
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
    list_display = ("id", "route", "user", "img_path", "is_active", "created_at")
    search_fields = ("route__id", "user__username")
    list_filter = ("is_active",)


@admin.register(UserFavoriteRoute)
class UserFavoriteRouteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "route", "spot", "is_active", "created_at")
    search_fields = ("user__username", "route__id", "spot__name")
    list_filter = ("is_active",)
