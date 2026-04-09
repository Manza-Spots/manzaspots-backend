from drf_spectacular.utils import OpenApiResponse, OpenApiExample
from core.responses.messages import AuthMessages, DatabaseMessages, ErrorMessages, ValidationMessages
from core.docs.serializers import ApiErrorSerializer, ApiValidationErrorSerializer

def simple_detail_response(example): 
    RESPONSE = {
        200: {
            "type": "object",
            "properties": {
                "detail": {
                    "type": "string",
                    "example": example
                }
            }
        }
    }
    return RESPONSE


def _api_error_response(description: str, detail: str, code_error: str = "") -> OpenApiResponse:
    return OpenApiResponse(
        response=ApiErrorSerializer,
        description=description,
        examples=[
            OpenApiExample(
                description,
                value={
                    "success": False,
                    "errors": {
                        "context": {"detail": detail},
                        "code_error": code_error
                    },
                    "data": "",
                    "message": None
                }
            )
        ]
    )

def _build_infra_response(description: str, detail: str) -> dict:
    return {
        "description": description,
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "errors": {
                        "context": {"detail": detail},
                        "code_error": ""
                    },
                    "data": "",
                    "message": None
                }
            }
        }
    }


# ── Infraestructura (hook global) ─────────────────────────────────────────────

INFRA_RESPONSES = {
    "500": _build_infra_response("Error inesperado", ErrorMessages.UNEXPECTED_ERROR),
    "502": _build_infra_response("Error en API externa", ErrorMessages.EXTERNAL_API_ERROR),
    "503": _build_infra_response("Servicio no disponible", ErrorMessages.SERVICE_UNAVAILABLE),
    "504": _build_infra_response("Timeout con servicio externo", ErrorMessages.SERVICE_TIMEOUT),
}

# ── Por contrato (decoradores) ────────────────────────────────────────────────

RESPONSE_401 = _api_error_response(
    "No autenticado",
    AuthMessages.LOGIN_REQUIRED + " / " + AuthMessages.CREDENTIALS_INVALID
)

RESPONSE_403 = _api_error_response(
    "Permiso denegado",
    AuthMessages.PERMISSION_DENIED
)

RESPONSE_404 = _api_error_response(
    "Recurso no encontrado",
    DatabaseMessages.RESOURCE_NOT_FOUND
)

RESPONSE_409 = _api_error_response(
    "Conflicto",
    DatabaseMessages.RESOURCE_EXISTS
)

RESPONSE_422 = _api_error_response(
    "Entidad no procesable",
    ValidationMessages.INVALID_FORMAT
)

RESPONSE_400_OAUTH = _api_error_response(
    "Error de autenticación OAuth",
    ErrorMessages.OAUTH_ERROR,
)

# ── Validación — estructura diferente ────────────────────────────────────────
def response_400( code_error: str) -> OpenApiResponse:
    return OpenApiResponse(
        response=ApiValidationErrorSerializer,
        description="Error de validación — los campos varían según el endpoint",
        examples=[
            OpenApiExample(
                "Campos inválidos",
                value={
                    "success": False,
                    "errors": {
                        "context": {
                            "field_name": ["Mensaje de error del campo."],
                        },
                        "code_error": code_error
                    },
                    "data": "",
                    "message": None
                }
            )
        ]
    )

def response_429(retry_after_seconds: int, code_error: str) -> OpenApiResponse:
    return OpenApiResponse(
        response=ApiErrorSerializer,
        description="Demasiadas solicitudes — límite excedido",
        examples=[
            OpenApiExample(
                "Rate limit excedido",
                value={
                    "success": False,
                    "errors": {
                        "context": {
                            "error": "rate_limit_exceeded",
                            "message": "Has excedido el límite de peticiones permitidas.",
                            "detail": "Por favor, espera antes de intentar nuevamente.",
                            "retry_after_seconds": retry_after_seconds
                        },
                        "code_error": code_error
                    },
                    "data": "",
                    "message": None
                }
            )
        ]
    )

