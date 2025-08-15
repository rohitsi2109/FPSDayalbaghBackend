from django.contrib import admin
from .models import BillingInvoice, BillingItem, BillingPayment

class BillingItemInline(admin.TabularInline):
    model = BillingItem
    extra = 0

class BillingPaymentInline(admin.TabularInline):
    model = BillingPayment
    extra = 0
    readonly_fields = ("created_at",)

@admin.register(BillingInvoice)
class BillingInvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "mode", "status", "order", "customer", "cashier", "total", "paid_amount", "created_at")
    list_filter = ("mode", "status", "cashier")
    search_fields = ("id", "order__id", "customer__username", "cashier__username")
    inlines = [BillingItemInline, BillingPaymentInline]
