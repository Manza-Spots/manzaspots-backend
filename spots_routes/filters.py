import django_filters
from .models import Route, RoutePhoto, Spot
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Polygon

class RouteFilter(django_filters.FilterSet):    
    user = django_filters.NumberFilter(field_name='user_id')
    difficulty = django_filters.CharFilter(
        field_name='difficulty__key',
        lookup_expr='iexact'
    )

    travel_mode = django_filters.CharFilter(
        field_name='travel_mode__key',
        lookup_expr='iexact'
    )

    class Meta:
        model = Route
        fields = ['user', 'difficulty', 'travel_mode']
        
class RoutePhotoFilter(django_filters.FilterSet):
    user = django_filters.NumberFilter(field_name='user_id')

    class Meta:
        model = RoutePhoto
        fields = ['user']

class SpotFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    
    status = django_filters.CharFilter(method="filter_status")

    lat = django_filters.NumberFilter(method="filter_by_radius")
    lng = django_filters.NumberFilter(method="filter_by_radius")
    radius = django_filters.NumberFilter(method="filter_by_radius")
    
    sw_lat = django_filters.NumberFilter(method="filter_bounding_box")
    sw_lng = django_filters.NumberFilter(method="filter_bounding_box")
    ne_lat = django_filters.NumberFilter(method="filter_bounding_box")
    ne_lng = django_filters.NumberFilter(method="filter_bounding_box")
    class Meta:
        model = Spot
        fields = ["name", "status"]

    def filter_status(self, queryset, name, value):
        request = self.request
        if request and request.user.is_staff:
            return queryset.filter(status__key=value)
        return queryset  

    def filter_by_radius(self, queryset, name, value):
        data = self.data
        if not all(k in data for k in ("lat", "lng")):
            return queryset

        point = Point(float(data["lng"]), float(data["lat"]), srid=4326)
        radius = float(data.get("radius", 5))
        
        return (
                    queryset
                    .filter(location__distance_lte=(point, D(km=radius)))
                    .annotate(distance=Distance("location", point))
                    .order_by("distance")
                )

    def filter_bounding_box(self, queryset, name, value):
            data = self.data
            try:
                sw_lat = float(data["sw_lat"])
                sw_lng = float(data["sw_lng"])
                ne_lat = float(data["ne_lat"])
                ne_lng = float(data["ne_lng"])
            except (KeyError, ValueError):
                return queryset  

            bbox = Polygon((
                (sw_lng, sw_lat),  
                (sw_lng, ne_lat),  
                (ne_lng, ne_lat),  
                (ne_lng, sw_lat),  
                (sw_lng, sw_lat),  
            ), srid=4326)

            return queryset.filter(location__within=bbox)
        