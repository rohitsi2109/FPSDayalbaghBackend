# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from decimal import Decimal
#
# from orders.models import Order
# from billing.models import BillingInvoice
#
# @receiver(post_save, sender=Order)
# def create_invoice_for_online_order(sender, instance: Order, created, **kwargs):
#     if not created:
#         return
#     # Only for ONLINE (automatic) orders — if your Order has a flag, check it here.
#     # If not, treat all created Orders as online.
#     BillingInvoice.objects.create(
#         mode=BillingInvoice.MODE_ONLINE,
#         status=BillingInvoice.STATUS_OPEN,
#         order=instance,
#         customer=getattr(instance, "user", None),
#         subtotal=Decimal(instance.total_amount or 0),
#         discount=Decimal("0"),
#         total=Decimal(instance.total_amount or 0),
#         paid_amount=Decimal("0"),
#     )

# billing/signals.py
from decimal import Decimal
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.conf import settings

from orders.models import Order
from .models import BillingInvoice, BillingPayment

# Track old status on Order so we can detect status changes cheaply
@receiver(pre_save, sender=Order)
def _billing_track_status(sender, instance: Order, **kwargs):
    if instance.pk:
        try:
            old = Order.objects.get(pk=instance.pk)
            instance._old_status_for_billing = getattr(old, "status", None)
        except Order.DoesNotExist:
            instance._old_status_for_billing = None
    else:
        instance._old_status_for_billing = None


# Which statuses should auto-generate/auto-capture invoices?
# You can override from settings.py:
# BILLING_TRIGGER_STATUSES = {"paid", "received"}
BILLING_TRIGGER_STATUSES = set(
    getattr(settings, "BILLING_TRIGGER_STATUSES", {"paid", "received"})
)
DEFAULT_ONLINE_METHOD = getattr(settings, "BILLING_ONLINE_METHOD", "online")


@receiver(post_save, sender=Order)
def _billing_invoice_on_paid(sender, instance: Order, created, **kwargs):
    if created:
        return

    old_status = (getattr(instance, "_old_status_for_billing", None) or "").lower()
    new_status = (getattr(instance, "status", None) or "").lower()

    # Only act when status actually changes into a trigger status
    if not new_status or new_status == old_status or new_status not in {s.lower() for s in BILLING_TRIGGER_STATUSES}:
        return

    # Idempotency: if an invoice for this order exists, reuse it
    inv = BillingInvoice.objects.filter(order=instance).order_by("id").first()
    total = Decimal(getattr(instance, "total_amount", 0) or 0)

    if not inv:
        inv = BillingInvoice.objects.create(
            mode=BillingInvoice.MODE_ONLINE,
            status=BillingInvoice.STATUS_OPEN,
            order=instance,
            customer=getattr(instance, "user", None),
            subtotal=total,
            discount=Decimal("0"),
            total=total,
            paid_amount=Decimal("0"),
        )

    # Capture any remaining amount as a payment once it became 'paid/received'
    due = (inv.total or Decimal("0")) - (inv.paid_amount or Decimal("0"))
    if due > 0:
        BillingPayment.objects.create(
            invoice=inv,
            method=DEFAULT_ONLINE_METHOD,
            amount=due,
            status="captured",
            txn_id=str(getattr(instance, "payment_id", ""))[:120],  # if your Order has one
            received_by=None,
        )
        # BillingPayment.save() bumps invoice.paid_amount and sets status to PAID when fully covered
        inv.refresh_from_db()

