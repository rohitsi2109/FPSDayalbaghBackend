# # from django.db.models.signals import post_save
# # from django.dispatch import receiver
# # from decimal import Decimal
# #
# # from orders.models import Order
# # from billing.models import BillingInvoice
# #
# # @receiver(post_save, sender=Order)
# # def create_invoice_for_online_order(sender, instance: Order, created, **kwargs):
# #     if not created:
# #         return
# #     # Only for ONLINE (automatic) orders — if your Order has a flag, check it here.
# #     # If not, treat all created Orders as online.
# #     BillingInvoice.objects.create(
# #         mode=BillingInvoice.MODE_ONLINE,
# #         status=BillingInvoice.STATUS_OPEN,
# #         order=instance,
# #         customer=getattr(instance, "user", None),
# #         subtotal=Decimal(instance.total_amount or 0),
# #         discount=Decimal("0"),
# #         total=Decimal(instance.total_amount or 0),
# #         paid_amount=Decimal("0"),
# #     )
#
# # billing/signals.py
# from decimal import Decimal
# from django.db.models.signals import pre_save, post_save
# from django.dispatch import receiver
# from django.conf import settings
#
# from orders.models import Order
# from .models import BillingInvoice, BillingPayment
#
# # Track old status on Order so we can detect status changes cheaply
# @receiver(pre_save, sender=Order)
# def _billing_track_status(sender, instance: Order, **kwargs):
#     if instance.pk:
#         try:
#             old = Order.objects.get(pk=instance.pk)
#             instance._old_status_for_billing = getattr(old, "status", None)
#         except Order.DoesNotExist:
#             instance._old_status_for_billing = None
#     else:
#         instance._old_status_for_billing = None
#
#
# # Which statuses should auto-generate/auto-capture invoices?
# # You can override from settings.py:
# # BILLING_TRIGGER_STATUSES = {"paid", "received"}
# BILLING_TRIGGER_STATUSES = set(
#     getattr(settings, "BILLING_TRIGGER_STATUSES", {"paid", "received"})
# )
# DEFAULT_ONLINE_METHOD = getattr(settings, "BILLING_ONLINE_METHOD", "online")
#
#
# @receiver(post_save, sender=Order)
# def _billing_invoice_on_paid(sender, instance: Order, created, **kwargs):
#     if created:
#         return
#
#     old_status = (getattr(instance, "_old_status_for_billing", None) or "").lower()
#     new_status = (getattr(instance, "status", None) or "").lower()
#
#     # Only act when status actually changes into a trigger status
#     if not new_status or new_status == old_status or new_status not in {s.lower() for s in BILLING_TRIGGER_STATUSES}:
#         return
#
#     # Idempotency: if an invoice for this order exists, reuse it
#     inv = BillingInvoice.objects.filter(order=instance).order_by("id").first()
#     total = Decimal(getattr(instance, "total_amount", 0) or 0)
#
#     if not inv:
#         inv = BillingInvoice.objects.create(
#             mode=BillingInvoice.MODE_ONLINE,
#             status=BillingInvoice.STATUS_OPEN,
#             order=instance,
#             customer=getattr(instance, "user", None),
#             subtotal=total,
#             discount=Decimal("0"),
#             total=total,
#             paid_amount=Decimal("0"),
#         )
#
#     # Capture any remaining amount as a payment once it became 'paid/received'
#     due = (inv.total or Decimal("0")) - (inv.paid_amount or Decimal("0"))
#     if due > 0:
#         BillingPayment.objects.create(
#             invoice=inv,
#             method=DEFAULT_ONLINE_METHOD,
#             amount=due,
#             status="captured",
#             txn_id=str(getattr(instance, "payment_id", ""))[:120],  # if your Order has one
#             received_by=None,
#         )
#         # BillingPayment.save() bumps invoice.paid_amount and sets status to PAID when fully covered
#         inv.refresh_from_db()
#


# billing/signals.py
from decimal import Decimal
from django.conf import settings
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from orders.models import Order  # uses your Orders app model
from .models import BillingInvoice, BillingItem, BillingPayment

# --- Configurable trigger/status/method mapping ---
# By default, we auto-bill when an Order turns "PAID".
# You can override in Django settings:
#   BILLING_TRIGGER_STATUSES = {"PAID"}       # case-insensitive
#   BILLING_ONLINE_METHOD    = "online"       # one of BillingPayment.METHOD_CHOICES
BILLING_TRIGGER_STATUSES = set(
    s.lower() for s in getattr(settings, "BILLING_TRIGGER_STATUSES", {"PAID"})
)
DEFAULT_ONLINE_METHOD = getattr(settings, "BILLING_ONLINE_METHOD", "online")

# --- Track old status for reliable change detection ---
@receiver(pre_save, sender=Order)
def _billing_track_old_status(sender, instance: Order, **kwargs):
    """
    Store previous status on the instance so post_save can detect transitions.
    We use a separate attribute to avoid colliding with your orders.signals.
    """
    if instance.pk:
        try:
            old = Order.objects.get(pk=instance.pk)
            instance._old_status_for_billing = getattr(old, "status", None)
        except Order.DoesNotExist:
            instance._old_status_for_billing = None
    else:
        instance._old_status_for_billing = None


@receiver(post_save, sender=Order)
def _billing_invoice_on_paid(sender, instance: Order, created, **kwargs):
    """
    When an existing Order's status changes into a trigger (e.g., PAID),
    create (or reuse) a BillingInvoice, copy items, recalc totals,
    and capture remaining due as a payment.
    """
    if created:
        return

    old_status = (getattr(instance, "_old_status_for_billing", None) or "").lower()
    new_status = (getattr(instance, "status", None) or "").lower()

    # Only act when the status actually *changes into* a trigger
    if not new_status or new_status == old_status or new_status not in BILLING_TRIGGER_STATUSES:
        return

    # Find or create invoice for this order (idempotency)
    inv = BillingInvoice.objects.filter(order=instance).order_by("id").first()

    if not inv:
        inv = BillingInvoice.objects.create(
            mode=BillingInvoice.MODE_ONLINE,
            status=BillingInvoice.STATUS_OPEN,
            order=instance,
            customer=getattr(instance, "user", None),
            # Store shipping snapshot even if user exists
            customer_name=getattr(instance, "shipping_name", "") or "",
            customer_phone=getattr(instance, "shipping_phone", "") or "",
            discount=Decimal("0"),
        )

    # If invoice has no items yet, copy order items into invoice (idempotent)
    if not inv.items.exists():
        # Use the snapshot from OrderItem (unit_price, quantity, etc.)
        order_items = getattr(instance, "items", None)
        if order_items is not None:
            rows = []
            for oi in order_items.all():
                rows.append(BillingItem(
                    invoice=inv,
                    product_id=getattr(oi.product, "id", None),
                    name=getattr(oi.product, "name", "") or "",
                    qty=Decimal(oi.quantity),
                    unit_price=Decimal(oi.unit_price),
                ))
            if rows:
                BillingItem.objects.bulk_create(rows)

    # Recalculate totals from invoice lines; fall back to order.total_amount if no lines
    inv.recalc(save=True)
    if inv.total == 0 and getattr(instance, "total_amount", None) not in (None, ""):
        # In case no lines or zero total, sync total from order as a safety net
        inv.subtotal = Decimal(getattr(instance, "total_amount", 0) or 0)
        inv.total = inv.subtotal - (inv.discount or 0)
        if inv.total < 0:
            inv.total = Decimal("0")
        inv.save(update_fields=["subtotal", "total"])

    # Capture any remaining due as a payment (idempotent: due<=0 means no duplicate)
    due = (inv.total or Decimal("0")) - (inv.paid_amount or Decimal("0"))
    if due > 0:
        BillingPayment.objects.create(
            invoice=inv,
            method=DEFAULT_ONLINE_METHOD,          # "online" by default
            amount=due,
            status="captured",
            txn_id=str(getattr(instance, "payment_id", ""))[:120],  # ok if your Order lacks payment_id
            received_by=None,
        )
        inv.refresh_from_db()  # BillingPayment.save() updates paid_amount & status
