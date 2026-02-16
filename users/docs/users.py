from core.docs.response import simple_detail_response


RESPONSE_ACTIVATE_USER = simple_detail_response("Usuario [username] activado.")
RESPONSE_DESACTIVATE_USER= simple_detail_response("Usuario [username] desactivado.")

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