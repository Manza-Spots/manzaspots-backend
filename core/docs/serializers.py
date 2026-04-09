from rest_framework import serializers


class ValidationContextSerializer(serializers.Serializer):
    """
    Contexto de errores de validación DRF.
    Los keys son los campos del serializer que fallaron.
    """
    username = serializers.ListField(child=serializers.CharField(), required=False)
    field_name = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Representa cualquier campo del serializer (email, password, etc.)"
    )


class DetailContextSerializer(serializers.Serializer):
    """Contexto para errores simples (no validación)."""
    detail = serializers.CharField()


class ErrorsValidationSerializer(serializers.Serializer):
    context = ValidationContextSerializer()
    code_error = serializers.CharField(
        help_text="Ruta del view que generó el error"
    )


class ErrorsDetailSerializer(serializers.Serializer):
    context = DetailContextSerializer()
    code_error = serializers.CharField()


class ApiValidationErrorSerializer(serializers.Serializer):
    """Estructura para errores de validación (campos inválidos)."""
    success = serializers.BooleanField(default=False)
    errors = ErrorsValidationSerializer()
    data = serializers.CharField(default="")
    message = serializers.CharField(allow_null=True, default=None)


class ApiErrorSerializer(serializers.Serializer):
    """Estructura para cualquier otro error (401, 403, 404, 500...)."""
    success = serializers.BooleanField(default=False)
    errors = ErrorsDetailSerializer()
    data = serializers.CharField(default="")
    message = serializers.CharField(allow_null=True, default=None)