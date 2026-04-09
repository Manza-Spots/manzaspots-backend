from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        email = user_email(sociallogin.user)
        if not email:
            return

        try:
            user = User.objects.get(email=email)

            for email_address in sociallogin.email_addresses:
                email_address.verified = True
                email_address.primary = True

            sociallogin.connect(request, user)

        except User.DoesNotExist:
            pass