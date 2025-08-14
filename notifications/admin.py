from django.contrib import admin
from .models import Device

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("token", "user", "platform", "is_admin", "last_seen")
    search_fields = ("token", "user__username", "user__phone", "user__id")
    list_filter = ("platform", "is_admin")
