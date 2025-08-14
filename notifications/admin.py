from django.contrib import admin
from .models import Device

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform', 'is_active', 'is_admin_receiver', 'created_at')
    list_filter = ('platform', 'is_active', 'is_admin_receiver')
    search_fields = ('user__phone', 'token')
