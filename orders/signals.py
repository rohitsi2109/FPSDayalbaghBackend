from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Order  # adapt to your actual Order model name
from notifications.models import Device
from notifications.fcm import send_to_tokens

User = get_user_model()

def _admin_tokens():
    return list(Device.objects.filter(is_admin=True).values_list("token", flat=True))

def _user_tokens(user):
    return list(Device.objects.filter(user=user, is_admin=False).values_list("token", flat=True))

@receiver(post_save, sender=Order)
def order_created_notify_admin(sender, instance: Order, created, **kwargs):
    if not created:
        return
    tokens = _admin_tokens()
    if not tokens:
        return
    title = f"New Order #{instance.id}"
    body = f"Amount ₹{instance.total_amount} • {instance.user and instance.user.name or ''}"
    send_to_tokens(tokens, title, body, data={"order_id": str(instance.id)})

# Track old status to detect change
@receiver(pre_save, sender=Order)
def order_status_track(sender, instance: Order, **kwargs):
    if instance.pk:
        try:
            old = Order.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Order)
def order_status_changed_notify_user(sender, instance: Order, created, **kwargs):
    if created:
        return  # handled above
    old_status = getattr(instance, "_old_status", None)
    if old_status is None or old_status == instance.status:
        return
    # Status changed -> notify the customer
    if instance.user_id:
        tokens = _user_tokens(instance.user)
        if tokens:
            title = f"Order #{instance.id} update"
            body = f"Status changed to {getattr(instance, 'status_display', instance.status)}"
            send_to_tokens(tokens, title, body, data={"order_id": str(instance.id)})
