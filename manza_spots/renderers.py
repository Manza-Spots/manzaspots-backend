# renderers.py
from rest_framework.renderers import JSONRenderer

class StandardJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context['response']
        view = renderer_context.get('view', None)
        
        module_name = None
        view_name = None
        message = None
        
        if view:
            module_name = view.__class__.__module__
            view_name = view.__class__.__name__
        
        if response.status_code >= 400:
            formatted_data = {
                'success': False,
                'errors': {
                    "context": data,
                    "code_error": "manza_spots." + module_name + "." + view_name,
                }, 
                "data": "",
                'message': message
            }
        else:
            formatted_data = {
                'success': True,
                'errors': {
                },
                'data': data,
                'message': message
            }
        
        return super().render(formatted_data, accepted_media_type, renderer_context)