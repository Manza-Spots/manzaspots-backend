import django_filters
from .models import Route, RoutePhoto


class RouteFilter(django_filters.FilterSet):
    user = django_filters.NumberFilter(field_name='user_id')
    spot = django_filters.NumberFilter(field_name='spot_id')
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
        fields = ['user', 'spot', 'difficulty', 'travel_mode']
        
class RoutePhotoFilter(django_filters.FilterSet):
    route = django_filters.NumberFilter(field_name='route_id')
    user = django_filters.NumberFilter(field_name='user_id')

    class Meta:
        model = RoutePhoto
        fields = ['route', 'user']
