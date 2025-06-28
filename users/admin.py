from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'phone', 'name', 'gender', 'is_staff')
    search_fields = ('phone', 'name')
    ordering = ('id',)
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal info', {'fields': ('name', 'gender', 'address')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'name', 'gender', 'address', 'password1', 'password2'),
        }),
    )

admin.site.register(User, UserAdmin)
