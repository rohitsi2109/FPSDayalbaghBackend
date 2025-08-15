from decimal import Decimal
from django.db import models
from django.conf import settings

class BillingInvoice(models.Model):
    MODE_ONLINE = "online"
    MODE_MANUAL = "manual"
    MODE_CHOICES = (
        (MODE_ONLINE, "Online"),
        (MODE_MANUAL, "Manual (POS)"),
    )

    STATUS_OPEN = "open"
    STATUS_PAID = "paid"
    STATUS_VOID = "void"
    STATUS_CHOICES = (
        (STATUS_OPEN, "Open"),
        (STATUS_PAID, "Paid"),
        (STATUS_VOID, "Void"),
    )

    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN)

    # Link to online order if present (kept nullable for POS invoices)
    order = models.ForeignKey(
        "orders.Order", null=True, blank=True, on_delete=models.SET_NULL, related_name="invoices"
    )

    # Optional relations
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="billing_invoices"
    )
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="pos_sales"
    )

    # amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def recalc(self, save=True):
        sub = Decimal("0")
        for it in self.items.all():
            sub += (it.qty * it.unit_price)
        self.subtotal = sub
        tot = sub - (self.discount or 0)
        if tot < 0:
            tot = Decimal("0")
        self.total = tot
        if save:
            self.save(update_fields=["subtotal", "total"])

    @property
    def is_paid(self):
        return (self.paid_amount or 0) >= (self.total or 0)

    def __str__(self):
        ref = f"Order#{self.order_id}" if self.order_id else f"POS#{self.pk}"
        return f"Invoice {ref} • {self.mode} • ₹{self.total}"


class BillingItem(models.Model):
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="items")
    product_id = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=255, blank=True, default="")
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    def line_total(self):
        return self.qty * self.unit_price


class BillingPayment(models.Model):
    METHOD_CHOICES = (
        ("online", "Online Gateway"),
        ("cash", "Cash"),
        ("upi", "UPI"),
        ("card", "Card"),
        ("cod", "Cash on Delivery"),
    )
    STATUS_CHOICES = (
        ("captured", "Captured"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="payments")
    method = models.CharField(max_length=16, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    txn_id = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="captured")
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="payments_taken"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.status == "captured":
            inv = self.invoice
            inv.paid_amount = (inv.paid_amount or 0) + self.amount
            inv.status = BillingInvoice.STATUS_PAID if inv.paid_amount >= inv.total else BillingInvoice.STATUS_OPEN
            inv.save(update_fields=["paid_amount", "status"])
