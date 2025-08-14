from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Order
from notifications.models import Device
from notifications.utils import send_fcm_multicast

def _user_tokens(user):
    return list(
        Device.objects.filter(user=user, is_active=True).values_list('token', flat=True)
    )

def _admin_tokens():
    return list(
        Device.objects.filter(is_admin_receiver=True, is_active=True).values_list('token', flat=True)
    )

@receiver(post_save, sender=Order)
def order_push_notifications(sender, instance: Order, created, **kwargs):
    # Run after commit to avoid sending for rolled-back transactions
    def _after_commit():
        try:
            total = float(instance.total_amount or 0)
        except Exception:
            total = 0.0

        # New order → notify shopkeepers
        if created:
            tokens = _admin_tokens()
            if tokens:
                title = f"New order #{instance.id}"
                u = getattr(instance, 'user', None)
                who = getattr(u, 'name', None) or getattr(u, 'phone', '') or 'Customer'
                body = f"{who} placed an order • ₹{total:.2f}"
                send_fcm_multicast(tokens, title, body, data={
                    'order_id': instance.id,
                    'event': 'order_created',
                })
            return

        # Status changed → notify customer
        try:
            prev = Order.objects.filter(pk=instance.pk).values('status').first()
        except Exception:
            prev = None
        if not prev:
            return
        old = (prev.get('status') or '').upper()
        new = (instance.status or '').upper()
        if old != new:
            u = getattr(instance, 'user', None)
            if not u:
                return
            tokens = _user_tokens(u)
            if not tokens:
                return
            title = f"Order #{instance.id} {instance.get_status_display() if hasattr(instance, 'get_status_display') else new.title()}"
            body  = f"Current status: {new.title()}"
            send_fcm_multicast(tokens, title, body, data={
                'order_id': instance.id,
                'old_status': old,
                'new_status': new,
                'event': 'order_status_changed',
            })

    transaction.on_commit(_after_commit)
