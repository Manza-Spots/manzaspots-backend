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