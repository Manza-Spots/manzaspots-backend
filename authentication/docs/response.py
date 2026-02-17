from core.docs.response import simple_detail_response
from core.responses.messages import AuthMessages, UserMessages


CONFIRM_NEW_PASSWORD_RESPONSE = simple_detail_response(AuthMessages.CONFIRM_NEW_PASSWORD)
EMAIL_SENT_IF_EXISTS_RESPONSE = simple_detail_response(UserMessages.EMAIL_SENT_IF_EXISTS)

LOGIN_RESPONSE = {
    200: {
        "type": "object",
        "properties": {
            "access": {"type": "string"},
            "refresh": {"type": "string"}
        }
    }
}

