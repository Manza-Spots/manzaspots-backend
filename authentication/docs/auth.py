# users/docs/auth.py
from core.docs.core import simple_detail_response


GOOGLE_LOGIN_REQUEST = {
    "application/json": {
        "type": "object",
        "properties": {
            "access_token": {
                "type": "string",
                "description": "Token emitido por Google"
            }
        },
        "required": ["access_token"]
    }
}

LOGIN_RESPONSE = {
    200: {
        "type": "object",
        "properties": {
            "access": {"type": "string"},
            "refresh": {"type": "string"}
        }
    }
}


REQUEST_NEW_PASSWORD_RESPONSE = simple_detail_response("Si el usuario existe, se enviará un correo con instrucciones.")
        
CONFIRM_NEW_PASSWORD_RESPONSE = simple_detail_response("Contraseña restablecida con éxito.")