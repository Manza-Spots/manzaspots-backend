from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """
        Se ejecuta antes de que allauth cree el usuario.
        Aquí interceptamos el caso del email existente.
        """
        if sociallogin.is_existing:
            return

        email = user_email(sociallogin.user)
        if not email:
            return

        try:
            user = User.objects.get(email=email)

            sociallogin.connect(request, user)

        except User.DoesNotExist:
            pass