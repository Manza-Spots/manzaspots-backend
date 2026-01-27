# users/admin.py
from pyexpat.errors import messages
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from users.models import UserProfile
admin.site.unregister(User)

#======================================================= PROFILE =============================================================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0
    readonly_fields = (
        "routes_created",
        "spots_created",
        "distance_traveled_km",
        "created_at",
        "updated_at",
    )
    
#======================================================= USER =============================================================
@admin.action(description="Desactivar usuarios seleccionados")
def deactivate_users(modeladmin, request, queryset):
    updated = queryset.filter(is_active=True).update(is_active=False)
    modeladmin.message_user(
        request,
        f"{updated} usuario(s) desactivado(s).",
        level=messages.SUCCESS,
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    actions = [deactivate_users]
    list_display = (
        "id",
        "username",
        "email",
        "is_active",
        "last_login",
        "date_joined",
    )
