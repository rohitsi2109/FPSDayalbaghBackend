from django.contrib import admin
from .models import Order, OrderItem, OrderStatus


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price", "line_total")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "payment_method", "total_amount", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("id", "user__name", "user__phone", "shipping_name", "shipping_phone")
    inlines = [OrderItemInline]
    readonly_fields = ("total_amount", "created_at", "updated_at")
