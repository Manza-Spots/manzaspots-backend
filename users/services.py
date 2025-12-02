from itsdangerous import URLSafeTimedSerializer
from django.conf import settings


class UsersService: 
    def generate_email_token(user):
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        return serializer.dumps({'user_id': user.id}, salt='email-confirm')

    def verify_email_token(token, max_age=3600):
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        try:
            data = serializer.loads(token, salt='email-confirm', max_age=max_age)
            return data['user_id']
        except Exception:
            return None
