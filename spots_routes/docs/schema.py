# core/docs/spots_schemas.py
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse
from core.docs.response import (
    RESPONSE_401,
    RESPONSE_403,
    RESPONSE_404,
    response_400,
    response_429,
)
from core.responses.messages import AuthMessages, RouteMessages, SpotMessages
from spots_routes.serializer import RoutePhotoCreateSerializer, RoutePhotoSerializer, RouteSerializer, SpotCaptionCreateSerializer, SpotCaptionSerializer, SpotSerializer, SpotUpdateSerializer, UserFavoriteRouteSerializer, UserFavoriteSpotSerializer
THROTTLE_HOUR = 3600

# ── Parámetros comunes ──────────────────────────────────────────────────────────

LIST_PARAMETERS = [
    OpenApiParameter(
        name='name',
        type=str,
        location=OpenApiParameter.QUERY,
        description='Filtrar spots por nombre (búsqueda parcial)',
        required=False
    ),
    OpenApiParameter(
        name='status',
        type=str,
        location=OpenApiParameter.QUERY,
        description='Filtrar por estado (solo administradores): PENDING, APPROVED, REJECTED',
        required=False
    )
]

# ── Schemas por acción ──────────────────────────────────────────────────────────

SPOT_LIST = {
    "summary": "Listar spots",
    "tags": ["spots"],
    "description": (
        "Obtiene la lista de spots del sistema.\n\n"
        "Los usuarios no autenticados y autenticados solo verán spots activos y aprobados.\n\n"
        "Los administradores pueden filtrar por estado."
    ),
    "parameters": LIST_PARAMETERS,
    "responses": {
        200: SpotSerializer(many=True),
        401: RESPONSE_401,
        403: RESPONSE_403,
    }
}

SPOT_RETRIEVE = {
    "summary": "Obtener detalle de spot",
    "tags": ["spots"],
    "description": "Obtiene la información detallada de un spot específico por su ID.",
    "responses": {
        200: SpotSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    }
}

SPOT_CREATE = {
    "summary": "Crear nuevo spot",
    "tags": ["spots"],
    "description": (
        "Crea un nuevo spot. El spot se crea en estado PENDING y será "
        "asignado automáticamente al usuario autenticado."
    ),
    "request": SpotSerializer,
    "responses": {
        201: OpenApiResponse(description=SpotMessages.SPOT_CREATED),
        400: lambda code: response_400(code),
        401: RESPONSE_401,
        403: RESPONSE_403,
        429: lambda code: response_429(THROTTLE_HOUR, code),
    }
}

SPOT_UPDATE = {
    "summary": "Actualizar spot completo",
    "tags": ["spots"],
    "description": (
        "Actualiza todos los campos de un spot.\n\n"
        "Solo el propietario del spot o un administrador pueden actualizarlo."
    ),
    "request": SpotUpdateSerializer,
    "responses": {
        200: SpotSerializer,
        400: lambda code: response_400(code),
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    }
}

SPOT_PARTIAL_UPDATE = {
    "summary": "Actualizar spot parcialmente",
    "tags": ["spots"],
    "description": (
        "Actualiza uno o más campos de un spot.\n\n"
        "Solo el propietario del spot o un administrador pueden actualizarlo."
    ),
    "request": SpotUpdateSerializer,
    "responses": {
        200: SpotSerializer,
        400: lambda code: response_400(code),
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    }
}

SPOT_DESTROY = {
    "summary": "Eliminar spot",
    "tags": ["spots"],
    "description": (
        "Elimina un spot del sistema (soft delete).\n\n"
        "Solo el propietario o un administrador pueden eliminarlo."
    ),
    "responses": {
        204: OpenApiResponse(description=SpotMessages.SPOT_DELETED),
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    }
}

# ── Actions personalizadas ─────────────────────────────────────────────────────

SPOT_AUTHORIZE = {
    "summary": "Autorizar spot",
    "tags": ["spots"],
    "description": (
        "Autoriza un spot cambiando su estado a APPROVED.\n\n"
        "Solo accesible para administradores.\n\n"
        "El spot se activa automáticamente al ser aprobado."
    ),
    "request": None,
    "responses": {
        200: SpotSerializer,
        403: OpenApiResponse(description=AuthMessages.PERMISSION_DENIED),
        404: OpenApiResponse(description="Spot no encontrado"),
    }
}

SPOT_DENY = {
    "summary": "Rechazar spot",
    "tags": ["spots"],
    "description": (
        "Rechaza un spot cambiando su estado a REJECTED.\n\n"
        "Solo accesible para administradores.\n\n"
        "Se requiere proporcionar una razón para el rechazo."
    ),
    "request": {
        "application/json": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Razón del rechazo"
                }
            },
            "required": ["reason"]
        }
    },
    "responses": {
        200: SpotSerializer,
        400: OpenApiResponse(description="Se requiere una razón para rechazar"),
        403: OpenApiResponse(description=AuthMessages.PERMISSION_DENIED),
        404: OpenApiResponse(description="Spot no encontrado"),
    }
}

SPOT_MY_SPOTS = {
    "summary": "Mis spots",
    "tags": ["spots"],
    "description": "Obtiene todos los spots creados por el usuario autenticado.",
    "responses": {
        200: SpotSerializer(many=True),
        401: RESPONSE_401,
    }
}

SPOT_ADD_TO_FAVORITES = {
    "summary": "Agregar a favoritos",
    "tags": ["spots", "spots-favorite"],
    "description": (
        "Agrega un spot a la lista de favoritos del usuario.\n\n"
        "Si el spot ya está en favoritos pero inactivo, lo reactiva."
    ),
    "request": None,
    "responses": {
        201: OpenApiResponse(description="Spot agregado a favoritos"),
        200: OpenApiResponse(description="Spot ya estaba en favoritos o fue reactivado"),
        401: RESPONSE_401,
        404: RESPONSE_404,
    }
}

SPOT_REMOVE_FROM_FAVORITES = {
    "summary": "Remover de favoritos",
    "tags": ["spots", "spots-favorite"],
    "description": (
        "Remueve un spot de la lista de favoritos del usuario (soft delete).\n\n"
        "El spot no se elimina, solo se marca como inactivo en favoritos."
    ),
    "request": None,
    "responses": {
        200: OpenApiResponse(description="Spot removido de favoritos"),
        401: RESPONSE_401,
        404: OpenApiResponse(description="Este spot no está en tus favoritos"),
    }
}

SPOT_FAVORITES = {
    "summary": "Agregar/Quitar favorito",
    "tags": ["spots", "spots-favorite"],
    "description": "Maneja el estado de favorito del spot (toggle)",
    "request": None,
    "responses": {
        201: OpenApiResponse(description="Spot agregado a favoritos"),
        200: OpenApiResponse(description="Spot ya estaba en favoritos"),
        204: OpenApiResponse(description="Spot removido de favoritos"),
        400: lambda code: response_400(code),
        401: RESPONSE_401,
        404: RESPONSE_404,
    }
}



USER_FAVORITE_SPOTS_LIST = {
    "summary": "Listar mis favoritos",
    "tags": ["spots-favorite"],
    "description": (
        "Obtiene la lista de spots favoritos del usuario autenticado.\n\n"
        "Solo muestra favoritos activos y spots no eliminados."
    ),
    "responses": {
        200: UserFavoriteSpotSerializer(many=True),
        401: RESPONSE_401,
    }
}




LIST_PARAMETERS = [
    OpenApiParameter(
        name='spot',
        type=int,
        location=OpenApiParameter.QUERY,
        description='ID del spot para filtrar sus captions',
        required=False
    )
]

SPOT_CAPTION_LIST = {
    "summary": "Listar captions",
    "tags": ["spot-captions"],
    "description": (
        "Obtiene la lista de captions (fotos) del spot compartido en el primer parámetro de ruta."
    ),
    "parameters": LIST_PARAMETERS,
    "responses": {
        200: SpotCaptionSerializer(many=True),
        401: RESPONSE_401,
    }
}

SPOT_CAPTION_RETRIEVE = {
    "summary": "Obtener caption",
    "tags": ["spot-captions"],
    "description": "Obtiene los detalles de un caption específico por su ID.",
    "responses": {
        200: SpotCaptionSerializer,
        401: RESPONSE_401,
        404: RESPONSE_404,
    }
}

SPOT_CAPTION_CREATE = {
    "summary": "Crear caption",
    "tags": ["spot-captions"],
    "description": (
        "Crea un nuevo caption (comentario) para un spot.\n\n"
        "El caption se asocia automáticamente al usuario autenticado.\n\n"
        "El ID del spot debe ser proporcionado en la URL como parámetro de ruta."
    ),
    "request": SpotCaptionCreateSerializer,
    "responses": {
        201: SpotCaptionSerializer,
        400: lambda code: response_400(code),
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    }
}

SPOT_CAPTION_UPDATE = {
    "summary": "Actualizar caption completo",
    "tags": ["spot-captions"],
    "description": (
        "Actualiza todos los campos de un caption.\n\n"
        "Solo el propietario del caption o un administrador pueden actualizarlo."
    ),
    "request": SpotCaptionCreateSerializer,
    "responses": {
        200: SpotCaptionSerializer,
        400: lambda code: response_400(code),
        401: RESPONSE_401,
        403: OpenApiResponse(description="No tienes permisos para editar este caption"),
        404: RESPONSE_404,
    }
}

SPOT_CAPTION_PARTIAL_UPDATE = {
    "summary": "Actualizar caption parcialmente",
    "tags": ["spot-captions"],
    "description": (
        "Actualiza uno o más campos de un caption.\n\n"
        "Solo el propietario del caption o un administrador pueden actualizarlo."
    ),
    "request": SpotCaptionCreateSerializer,
    "responses": {
        200: SpotCaptionSerializer,
        400: lambda code: response_400(code),
        401: RESPONSE_401,
        403: OpenApiResponse(description="No tienes permisos para editar este caption"),
        404: RESPONSE_404,
    }
}

SPOT_CAPTION_DESTROY = {
    "summary": "Eliminar caption",
    "tags": ["spot-captions"],
    "description": (
        "Elimina un caption.\n\n"
        "Solo el propietario o un administrador pueden eliminarlo.\n\n"
        "Este endpoint realizará la eliminación del registro."
    ),
    "responses": {
        204: OpenApiResponse(description="Caption eliminado correctamente"),
        401: RESPONSE_401,
        403: OpenApiResponse(description="No tienes permisos para eliminar este caption"),
        404: RESPONSE_404,
    }
}




NESTED_PATH_PARAMS = [
    OpenApiParameter(
        name='spot_pk',
        type=int,
        location=OpenApiParameter.PATH,
        description='ID del spot',
        required=True
    ),
    OpenApiParameter(
        name='route_pk',
        type=int,
        location=OpenApiParameter.PATH,
        description='ID de la ruta',
        required=True
    )
]

ROUTE_PHOTO_FILTER_PARAMS = [
    OpenApiParameter(
        name='route',
        type=int,
        location=OpenApiParameter.QUERY,
        description='Filtrar fotos por ID de ruta',
        required=False
    ),
    OpenApiParameter(
        name='user',
        type=int,
        location=OpenApiParameter.QUERY,
        description='Filtrar fotos por ID de usuario',
        required=False
    )
]

# ── Schemas por acción ──────────────────────────────────────────────────────────

ROUTE_PHOTO_LIST = {
    "summary": "Listar fotos de rutas",
    "tags": ["routes-photos"],
    "parameters": NESTED_PATH_PARAMS + ROUTE_PHOTO_FILTER_PARAMS,
    "description": (
        "Obtiene una lista de todas las fotos de rutas de un spot indicado en el query parameter.\n\n"
        "Soporta filtrado por ruta, usuario, etc."
    ),
    "responses": {
        200: RoutePhotoSerializer(many=True),
        401: RESPONSE_401,
        403: RESPONSE_403,
    }
}

ROUTE_PHOTO_RETRIEVE = {
    "summary": "Obtener detalle de foto",
    "tags": ["routes-photos"],
    "parameters": NESTED_PATH_PARAMS,
    "description": "Obtiene los detalles de una foto específica.",
    "responses": {
        200: RoutePhotoSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    }
}

ROUTE_PHOTO_CREATE = {
    "summary": "Subir nueva foto a ruta",
    "tags": ["routes-photos"],
    "parameters": NESTED_PATH_PARAMS,
    "description": (
        "Sube una nueva foto asociada a una ruta.\n\n"
        "- El usuario se asigna automáticamente\n"
        "- Debe incluir el ID de la ruta como parámetro de ruta\n"
        "- Requiere autenticación\n"
        "- Formato: multipart/form-data para subir imagen"
    ),
    "request": RoutePhotoCreateSerializer,
    "responses": {
        201: RoutePhotoSerializer,
        400: lambda code: response_400(code),
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    }
}

ROUTE_PHOTO_UPDATE = {
    "summary": "Actualizar foto de ruta (completo)",
    "tags": ["routes-photos"],
    "parameters": NESTED_PATH_PARAMS,
    "description": (
        "Actualiza todos los campos de una foto de ruta.\n\n"
        "Solo el propietario de la foto o un administrador pueden actualizarla."
    ),
    "request": RoutePhotoCreateSerializer,
    "responses": {
        200: RoutePhotoSerializer,
        400: lambda code: response_400(code),
        401: RESPONSE_401,
        403: OpenApiResponse(description="No tienes permisos para editar esta foto"),
        404: RESPONSE_404,
    }
}

ROUTE_PHOTO_PARTIAL_UPDATE = {
    "summary": "Actualizar foto de ruta (parcial)",
    "tags": ["routes-photos"],
    "parameters": NESTED_PATH_PARAMS,
    "description": (
        "Actualiza uno o más campos de una foto de ruta.\n\n"
        "Solo el propietario de la foto o un administrador pueden actualizarla."
    ),
    "request": RoutePhotoCreateSerializer,
    "responses": {
        200: RoutePhotoSerializer,
        400: lambda code: response_400(code),
        401: RESPONSE_401,
        403: OpenApiResponse(description="No tienes permisos para editar esta foto"),
        404: RESPONSE_404,
    }
}

ROUTE_PHOTO_DESTROY = {
    "summary": "Eliminar foto de ruta",
    "tags": ["routes-photos"],
    "parameters": NESTED_PATH_PARAMS,
    "description": (
        "Elimina una foto de ruta.\n\n"
        "Solo el propietario o un administrador pueden eliminarla.\n\n"
        "La operación eliminará el recurso correspondiente."
    ),
    "responses": {
        204: OpenApiResponse(description="Foto eliminada correctamente"),
        401: RESPONSE_401,
        403: OpenApiResponse(description="No tienes permisos para eliminar esta foto"),
        404: RESPONSE_404,
    }
}

# ── Action personalizada ──────────────────────────────────────────────────────

ROUTE_PHOTO_MY_PHOTOS = {
    "summary": "Obtener mis fotos",
    "tags": ["routes-photos"],
    "parameters": NESTED_PATH_PARAMS,
    "description": (
        "Obtiene solo las fotos subidas por el usuario autenticado.\n\n"
        "- Filtrado automático por usuario\n"
        "- Requiere autenticación\n"
        "- Incluye todas las relaciones (ruta, usuario)"
    ),
    "responses": {
        200: RoutePhotoSerializer(many=True),
        401: RESPONSE_401,
    }
}





USER_FAVORITE_ROUTES_LIST = {
    "summary": "Listar rutas favoritas del usuario",
    "tags": ["routes-favorite"],
    "description": (
        "Obtiene la lista de rutas marcadas como favoritas por el usuario autenticado.\n\n"
        "- Solo muestra favoritos activos\n"
        "- Requiere autenticación\n"
        "- Incluye información completa de cada ruta"
    ),
    "responses": {
        200: OpenApiResponse(
            description=RouteMessages.FAVORITE_ROUTES_LIST,
            response=UserFavoriteRouteSerializer(many=True)
        ),
        401: RESPONSE_401,
    }
}


ROUTE_FILTER_PARAMS = [
    OpenApiParameter(
        name='difficulty',
        type=str,
        location=OpenApiParameter.QUERY,
        description='Filtrar por nivel de dificultad (Fácil, Media, Difícil)',
        required=False
    ),
    OpenApiParameter(
        name='travel_mode',
        type=str,
        location=OpenApiParameter.QUERY,
        description='Filtrar por modo de viaje (Caminata, Bicicleta, Auto)',
        required=False
    ),
    OpenApiParameter(
        name='duration_min',
        type=int,
        location=OpenApiParameter.QUERY,
        description='Duración mínima en minutos',
        required=False
    ),
    OpenApiParameter(
        name='duration_max',
        type=int,
        location=OpenApiParameter.QUERY,
        description='Duración máxima en minutos',
        required=False
    ),
    OpenApiParameter(
        name='expand',
        type=str,
        location=OpenApiParameter.QUERY,
        description='Campos adicionales a incluir (ej: photos)',
        required=False
    )
]

# ── Schemas por acción ──────────────────────────────────────────────────────────

ROUTE_LIST = {
    "summary": "Listar rutas",
    "tags": ["routes"],
    "description": (
        "Obtiene una lista de todas las rutas activas.\n\n"
        "- Soporta filtrado mediante query params\n"
        "- Por defecto no incluye fotos (optimización de rendimiento)\n"
        "- Use `?expand=photos` para incluir fotos en la respuesta\n"
        "- Requiere autenticación solo para crear/editar"
    ),
    "parameters": ROUTE_FILTER_PARAMS,
    "responses": {
        200: RouteSerializer(many=True),
        401: RESPONSE_401,
        403: RESPONSE_403,
    }
}

ROUTE_RETRIEVE = {
    "summary": "Obtener detalle de ruta",
    "tags": ["routes"],
    "description": (
        "Obtiene los detalles completos de una ruta específica, incluyendo fotos."
    ),
    "responses": {
        200: RouteSerializer,
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    }
}

ROUTE_CREATE = {
    "summary": "Crear nueva ruta",
    "tags": ["routes"],
    "description": (
        "Crea una nueva ruta asociada a un spot.\n\n"
        "**Notas:**\n"
        "- El usuario se asigna automáticamente del token de autenticación\n"
        "- El spot se obtiene del parámetro de la URL (spot_pk)\n"
        "- Requiere autenticación"
    ),
    "request": RouteSerializer,
    "responses": {
        201: RouteSerializer,
        400: lambda code: response_400(code),
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    }
}

ROUTE_UPDATE = {
    "summary": "Actualizar ruta completa",
    "tags": ["routes"],
    "description": (
        "Actualiza todos los campos de una ruta.\n\n"
        "Solo el propietario puede editar."
    ),
    "request": RouteSerializer,
    "responses": {
        200: RouteSerializer,
        400: lambda code: response_400(code),
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    }
}

ROUTE_PARTIAL_UPDATE = {
    "summary": "Actualizar ruta parcialmente",
    "tags": ["routes"],
    "description": (
        "Actualiza campos específicos de una ruta.\n\n"
        "Solo el propietario puede editar."
    ),
    "request": RouteSerializer,
    "responses": {
        200: RouteSerializer,
        400: lambda code: response_400(code),
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    }
}

ROUTE_DESTROY = {
    "summary": "Eliminar ruta (soft delete)",
    "tags": ["routes"],
    "description": (
        "Marca la ruta como inactiva en lugar de eliminarla permanentemente.\n\n"
        "Solo el propietario puede eliminar su ruta."
    ),
    "responses": {
        204: OpenApiResponse(description="Ruta eliminada exitosamente"),
        401: RESPONSE_401,
        403: RESPONSE_403,
        404: RESPONSE_404,
    }
}

# ── Actions personalizadas ─────────────────────────────────────────────────────

ROUTE_ADD_FAVORITE = {
    "summary": "Añadir ruta a favoritos",
    "tags": ["routes", "routes-favorite"],
    "description": (
        "Marca una ruta como favorita para el usuario autenticado.\n\n"
        "**Comportamiento:**\n"
        "- Si ya existe como favorito pero estaba inactivo, lo reactiva\n"
        "- Si ya está activo, retorna error 400\n"
        "- Requiere autenticación"
    ),
    "request": None,
    "responses": {
        200: OpenApiResponse(description="Ruta reactivada en favoritos"),
        201: OpenApiResponse(description="Ruta añadida a favoritos exitosamente"),
        400: OpenApiResponse(description="La ruta ya está en favoritos"),
        401: RESPONSE_401,
        404: RESPONSE_404,
    }
}

ROUTE_REMOVE_FAVORITE = {
    "summary": "Eliminar ruta de favoritos",
    "tags": ["routes", "routes-favorite"],
    "description": (
        "Elimina una ruta de los favoritos del usuario (soft delete).\n\n"
        "**Comportamiento:**\n"
        "- Marca el favorito como inactivo\n"
        "- Si no existe o ya está inactivo, retorna 404\n"
        "- Requiere autenticación"
    ),
    "request": None,
    "responses": {
        200: OpenApiResponse(description="Ruta eliminada de favoritos exitosamente"),
        401: RESPONSE_401,
        404: OpenApiResponse(description="La ruta no está en favoritos"),
    }
}