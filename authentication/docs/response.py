from core.docs.response import simple_detail_response
from core.docs.serializers import ApiErrorSerializer
from core.responses.messages import AuthMessages, UserMessages
from drf_spectacular.utils import OpenApiResponse, OpenApiExample


PASSWORD_RESET_SUCCESS_RESPONSE = simple_detail_response(AuthMessages.PASSWORD_RESET_SUCCESS)
EMAIL_SENT_IF_EXISTS_RESPONSE = simple_detail_response(UserMessages.EMAIL_SENT_IF_EXISTS)

JWT_SUCCES_RESPONSE = OpenApiResponse(
        response=ApiErrorSerializer,
        description="Autenticacion Exitosa",
        examples=[
            OpenApiExample(
                "Autenticacion Exitosa",
                value={
                    "success": True,
                        "errors": {},
                        "data": {
                            "access": "eyJhbGciO...",
                            "refresh": "eyJhbGci...",
                            "user": {
                                "id": "",
                                "username": "",
                                "email": "",
                                "first_name": "",
                                "last_name": ""
                            }
                        },
                        "message": None
                }
            )
        ]
    )

