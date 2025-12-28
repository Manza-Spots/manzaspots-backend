from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.utils.html import format_html
from django.contrib.admin import DateFieldListFilter
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
class SpotAdmin(gis_admin.GISModelAdmin):
    # UBICACION DE MANZA
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
        "status_badge",
        "routes_count",
        "favorites_count",
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
                return format_html('<span style="color:red;">Imagen no encontrada</span>')
        return format_html('<span style="color:gray;">Sin imagen</span>')
    
    thumbnail_preview.short_description = "Thumbnail"

    def location_display(self, obj):
        if not obj.location:
            return "-"
        return f"{obj.location.y:.6f}, {obj.location.x:.6f}"
    
    location_display.short_description = "Coordenadas"
    
    def status_badge(self, obj):
        """Badge visual para el estado"""
        colors = {
            'PENDING': '#ffc107',
            'APPROVED': '#28a745',
            'REJECTED': '#dc3545',
        }
        color = colors.get(obj.status.key, '#6c757d')
        return format_html(
            '<span style="background-color:{}; color:white; padding:4px 10px; border-radius:12px; font-size:11px;">{}</span>',
            color, obj.status.name
        )
    status_badge.short_description = "Estado"
    
    def routes_count(self, obj):
        count = obj.routes.filter(is_active=True).count()
        return format_html('🛤️ {}', count) if count > 0 else '-'
    routes_count.short_description = "Rutas"
    
    def favorites_count(self, obj):
        count = obj.favorited_by.filter(is_active=True).count()
        return format_html('⭐ {}', count) if count > 0 else '-'
    favorites_count.short_description = "Favoritos"


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
    list_display = ("id", "name", "key", "hex_color_preview", "is_active")
    search_fields = ("name", "key")
    list_filter = ("is_active",)
    
    def hex_color_preview(self, obj):
        """Preview del color"""
        return format_html(
            '<div style="background-color:{}; width:50px; height:20px; border-radius:3px; border:1px solid #ddd;"></div>',
            obj.hex_color
        )
    hex_color_preview.short_description = "Color"


@admin.register(TravelMode)
class TravelModeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "key", "is_active")
    search_fields = ("name", "key")
    list_filter = ("is_active",)


class RoutePhotoInline(admin.TabularInline):
    model = RoutePhoto
    extra = 0
    readonly_fields = ("created_at", "updated_at", "thumbnail_inline")
    fields = ("img_path", "thumbnail_inline", "location", "is_active", "created_at")
    
    def thumbnail_inline(self, obj):
        """Miniatura en el inline"""
        if obj.img_path:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px;" />',
                obj.img_path.url
            )
        return "Sin imagen"
    thumbnail_inline.short_description = "Preview"


@admin.action(description="✅ Activar rutas seleccionadas")
def activar_routes(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="❌ Desactivar rutas seleccionadas")
def desactivar_routes(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.register(Route)
class RouteAdmin(gis_admin.GISModelAdmin):
    """Admin para Routes con visualización del PATH geográfico"""
    
    # Configuración del mapa GIS para el path
    gis_widget_kwargs = {
        'attrs': {
            'default_zoom': 13,           # Más zoom para ver mejor
            'default_lat': 19.0519,       # Centro Manzanillo
            'default_lon': -104.3186,
            'map_width': 800,             # Ancho del mapa
            'map_height': 500,            # Alto del mapa
            'scrollable': False,          # Evita zoom accidental
        },
    }
    
    # Tipo de mapa (puedes cambiar la capa base)
    map_template = 'gis/admin/openlayers.html'
    openlayers_url = 'https://cdn.jsdelivr.net/npm/ol@v7.3.0/dist/ol.js'
    
    list_display = (
        "id",
        "user",
        "spot",
        "difficulty_colored",
        "travel_mode",
        "distance",
        "path_preview",
        "start_point",
        "end_point",
        "photos_count",
        "is_active",
        "created_at",
    )
    
    search_fields = ("user__username", "spot__name")
    list_filter = (
        "difficulty", 
        "travel_mode", 
        "is_active",
        ("created_at", DateFieldListFilter),
    )
    
    readonly_fields = (
        "created_at", 
        "updated_at",
        "path_info",
    )
    
    inlines = [RoutePhotoInline]
    actions = [activar_routes, desactivar_routes]
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def get_queryset(self, request):
        """Optimización de queries"""
        return (
            super().get_queryset(request)
            .select_related("user", "spot", "difficulty", "travel_mode")
            .prefetch_related("photo")
        )

    def difficulty_colored(self, obj):
        """Muestra dificultad con su color"""
        if obj.difficulty:
            return format_html(
                '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
                obj.difficulty.hex_color,
                obj.difficulty.name
            )
        return "-"
    difficulty_colored.short_description = "Dificultad"
    
    def path_preview(self, obj):
        """Vista previa simple del path"""
        if obj.path:
            num_points = len(obj.path.coords)
            return format_html(
                '<span style="background: #e3f2fd; padding: 2px 6px; border-radius: 3px;" title="{}">📍 {} pts</span>',
                f"{num_points} coordenadas en la ruta",
                num_points
            )
        return format_html('<span style="color: #999;">Sin ruta</span>')
    path_preview.short_description = "Path"
    
    def start_point(self, obj):
        """Punto inicial de la ruta"""
        if obj.path and len(obj.path.coords) > 0:
            lon, lat = obj.path.coords[0]
            lat_str = f"{lat:.5f}"
            lon_str = f"{lon:.5f}"
            return format_html(
                '<span style="font-family: monospace; font-size: 11px;">{}, {}</span>',
                lat_str, lon_str
            )
        return "-"
    start_point.short_description = "🟢 Inicio"
    
    def end_point(self, obj):
        """Punto final de la ruta"""
        if obj.path and len(obj.path.coords) > 0:
            lon, lat = obj.path.coords[-1]
            lat_str = f"{lat:.5f}"
            lon_str = f"{lon:.5f}"
            return format_html(
                '<span style="font-family: monospace; font-size: 11px;">{}, {}</span>',
                lat_str, lon_str
            )
        return "-"
    end_point.short_description = "🔴 Fin"
    
    def photos_count(self, obj):
        """Contador de fotos"""
        count = obj.photo.filter(is_active=True).count()
        if count > 0:
            return format_html('<span style="color: green;">📷 {}</span>', count)
        return format_html('<span style="color: gray;">-</span>')
    photos_count.short_description = "Fotos"
    
    def path_info(self, obj):
        """Información detallada del path para la página de detalle"""
        if not obj.path:
            return format_html('<p style="color: #999;">Sin información de ruta</p>')
        
        num_points = len(obj.path.coords)
        length_km = obj.distance
        
        # Calcular centro aproximado
        lons = [coord[0] for coord in obj.path.coords]
        lats = [coord[1] for coord in obj.path.coords]
        center_lon = sum(lons) / len(lons)
        center_lat = sum(lats) / len(lats)
        
        # Formatear coordenadas
        start_lat = f"{obj.path.coords[0][1]:.6f}"
        start_lon = f"{obj.path.coords[0][0]:.6f}"
        end_lat = f"{obj.path.coords[-1][1]:.6f}"
        end_lon = f"{obj.path.coords[-1][0]:.6f}"
        center_lat_str = f"{center_lat:.6f}"
        center_lon_str = f"{center_lon:.6f}"
        
        html = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">
            <h4 style="margin-top:0; color: #495057;">📊 Información del Path</h4>
            <table style="width: 100%; margin-top: 10px;">
                <tr>
                    <td style="padding: 5px;"><strong>Puntos totales:</strong></td>
                    <td style="padding: 5px;">{num_points}</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><strong>Distancia:</strong></td>
                    <td style="padding: 5px;">{length_km} km</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><strong>Punto inicial:</strong></td>
                    <td style="padding: 5px; font-family: monospace;">{start_lat}, {start_lon}</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><strong>Punto final:</strong></td>
                    <td style="padding: 5px; font-family: monospace;">{end_lat}, {end_lon}</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><strong>Centro aprox:</strong></td>
                    <td style="padding: 5px; font-family: monospace;">{center_lat_str}, {center_lon_str}</td>
                </tr>
            </table>
        </div>
        """
        return format_html(html)
    path_info.short_description = "📍 Detalles del Path"


@admin.register(RoutePhoto)
class RoutePhotoAdmin(gis_admin.GISModelAdmin):
    gis_widget_kwargs = {
        'attrs': {
            'default_zoom': 15,
            'default_lat': 19.0519,
            'default_lon': -104.3186,
        },
    }
    list_display = (
        "id", 
        "route", 
        "user", 
        "image_preview", 
        "location_coords",
        "is_active", 
        "created_at"
    )
    
    search_fields = ("route__id", "user__username")
    list_filter = ("is_active", "created_at")
    readonly_fields = ("image_preview_large", "location_display", "created_at", "updated_at")
    
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
    
    def location_coords(self, obj):
        """Coordenadas donde se tomó la foto"""
        if obj.location:
            lat_str = f"{obj.location.y:.5f}"
            lon_str = f"{obj.location.x:.5f}"
            return format_html(
                '<span style="font-family: monospace; font-size: 11px;">📍 {}, {}</span>',
                lat_str, lon_str
            )
        return format_html('<span style="color: gray;">Sin ubicación</span>')
    location_coords.short_description = "Ubicación"
    
    def location_display(self, obj):
        """Vista detallada de ubicación"""
        if not obj.location:
            return format_html('<p style="color: #999;">Sin ubicación registrada</p>')
        
        lat_str = f"{obj.location.y}"
        lon_str = f"{obj.location.x}"
        
        return format_html(
            '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6;">'
            '<h4 style="margin-top:0;">📍 Coordenadas de la Foto</h4>'
            '<p><strong>Latitud:</strong> {}</p>'
            '<p><strong>Longitud:</strong> {}</p>'
            '<p style="margin-bottom:0;"><a href="https://www.google.com/maps?q={},{}" target="_blank" '
            'style="color: #007bff; text-decoration: none;">🗺️ Ver en Google Maps</a></p>'
            '</div>',
            lat_str, lon_str, lat_str, lon_str
        )
    location_display.short_description = "Coordenadas"


@admin.register(UserFavoriteRoute)
class UserFavoriteRouteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "route", "is_active", "created_at")
    search_fields = ("user__username", "route__id", "route__spot__name")
    list_filter = ("is_active",)