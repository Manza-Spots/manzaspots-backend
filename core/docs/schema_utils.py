from drf_spectacular.utils import extend_schema
import copy

def auto_schema(**schema_kwargs):
    def decorator(cls):
        # Deep copy — copia todo, incluyendo dicts anidados
        kwargs = copy.deepcopy(schema_kwargs)
        
        full_code = f"{cls.__module__}.{cls.__qualname__}"

        description = kwargs.get('description', '')
        kwargs['description'] = f"{description}\n\n**Code:** `{full_code}`"

        responses = kwargs.get('responses', {})
        kwargs['responses'] = {
            status: response(full_code) if callable(response) else response
            for status, response in responses.items()
        }

        return extend_schema(**kwargs)(cls)
    return decorator