# admin.py
from django.contrib import admin
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.admin import SocialAccountAdmin

# Desregistrar
admin.site.unregister(SocialAccount)

# Parchear el método __str__
def custom_str(self):
    return f"{str(self.user)} - {str(self.provider)}"

SocialAccount.__str__ = custom_str

# Volver a registrar
admin.site.register(SocialAccount, SocialAccountAdmin)