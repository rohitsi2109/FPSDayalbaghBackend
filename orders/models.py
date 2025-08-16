# from django.conf import settings
# from django.db import models
# from django.utils import timezone
#
#
# class OrderStatus(models.TextChoices):
#     PENDING = "PENDING", "Pending"
#     PAID = "PAID", "Paid"
#     SHIPPED = "SHIPPED", "Shipped"
#     COMPLETED = "COMPLETED", "Completed"
#     CANCELLED = "CANCELLED", "Cancelled"
#
#
# class Order(models.Model):
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="orders"
#     )
#     status = models.CharField(
#         max_length=12,
#         choices=OrderStatus.choices,
#         default=OrderStatus.PENDING
#     )
#     payment_method = models.CharField(
#         max_length=10,
#         choices=[("COD", "Cash on Delivery"), ("ONLINE", "Online")],
#         default="COD",
#     )
#
#     # price snapshot is stored on OrderItem; we keep only total here
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#
#     # Simple shipping snapshot
#     shipping_name = models.CharField(max_length=120)
#     shipping_phone = models.CharField(max_length=20)
#     address_line1 = models.CharField(max_length=255)
#     address_line2 = models.CharField(max_length=255, blank=True, default="")
#     city = models.CharField(max_length=100)
#     state = models.CharField(max_length=100)
#     pincode = models.CharField(max_length=12)
#
#     created_at = models.DateTimeField(default=timezone.now)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     class Meta:
#         ordering = ["-created_at"]
#
#     def __str__(self):
#         return f"Order #{self.id} - {self.user} - {self.status}"
#
#
# class OrderItem(models.Model):
#     from products.models import Product
#
#     order = models.ForeignKey(
#         Order, on_delete=models.CASCADE, related_name="items"
#     )
#     product = models.ForeignKey(
#         "products.Product", on_delete=models.PROTECT, related_name="order_items"
#     )
#     quantity = models.PositiveIntegerField()
#     unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # snapshot
#     line_total = models.DecimalField(max_digits=10, decimal_places=2)
#
#     def __str__(self):
#         return f"{self.product.name} x {self.quantity} (Order #{self.order_id})"

from django.conf import settings
from django.db import models
from django.utils import timezone


class OrderStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PAID = "PAID", "Paid"
    SHIPPED = "SHIPPED", "Shipped"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class OrderSource(models.TextChoices):
    ONLINE = "ONLINE", "Online"
    POS = "POS", "In-store (POS)"


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(
        max_length=12,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    # Where did this order come from?
    source = models.CharField(
        max_length=8,
        choices=OrderSource.choices,
        default=OrderSource.ONLINE,
        db_index=True,
    )
    payment_method = models.CharField(
        max_length=10,
        choices=[("COD", "Cash on Delivery"), ("ONLINE", "Online")],
        default="COD",
    )

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Shipping snapshot
    shipping_name = models.CharField(max_length=120)
    shipping_phone = models.CharField(max_length=20, db_index=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=12)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} - {self.user} - {self.status} - {self.source}"


class OrderItem(models.Model):
    # snapshot of product & price at purchase time
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        "products.Product", on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} (Order #{self.order_id})"
