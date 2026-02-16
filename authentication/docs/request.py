from core.docs.response import simple_detail_response


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

FACEBOOK_LOGIN_REQUEST = {
    "application/json": {
        "type": "object",
        "properties": {
            "access_token": {
                "type": "string",
                "description": "Token emitido por facebook"
            }
        },
        "required": ["access_token"]
    }
}


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