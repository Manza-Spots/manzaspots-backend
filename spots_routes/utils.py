from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes

NESTED_PATH_PARAMS = [
    OpenApiParameter(
        name="spot_pk",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.PATH,
        description="ID del spot",
    ),
    OpenApiParameter(
        name="route_pk",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.PATH,
        description="ID de la ruta",
    ),
]

ROUTE_FILTER_PARAMS = [
    OpenApiParameter(
        name="user",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description="ID del usuario que creó la ruta"
    ),
    OpenApiParameter(
        name="spot",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description="ID del spot"
    ),
    OpenApiParameter(
        name="difficulty",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="Clave de dificultad (easy, medium, hard)"
    ),
    OpenApiParameter(
        name="travel_mode",
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description="Clave del modo de viaje (walk, bike, car)"
    ),
    OpenApiParameter(
        name='expand',
        type=OpenApiTypes.STR,
        location=OpenApiParameter.QUERY,
        description='Expandir relaciones del modelo (ej: "photos" para incluir fotos)',
        required=False
    )
]

ROUTE_PHOTO_FILTER_PARAMS = [
    OpenApiParameter(
        name="route",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description="ID de la ruta"
    ),
    OpenApiParameter(
        name="user",
        type=OpenApiTypes.INT,
        location=OpenApiParameter.QUERY,
        description="ID del usuario"
    ),
]

RESEND_CONFIRMATION_EMAIL_REQUEST = {
    "application/json": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "Correo que se verificara"
            }
        },
        "required": ["email"]
    }
}