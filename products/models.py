import io

from PIL import Image
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.utils import timezone


MAX_IMAGE_DIM = 1200   # px on the longest side
JPEG_QUALITY = 80


def _compress_to_jpeg(field_file):
    img = Image.open(field_file)
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    buf.seek(0)

    base = field_file.name.rsplit(".", 1)[0] if "." in field_file.name else field_file.name
    return InMemoryUploadedFile(
        buf,
        field_name="image",
        name=f"{base}.jpg",
        content_type="image/jpeg",
        size=buf.getbuffer().nbytes,
        charset=None,
    )


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=800)
    stock = models.PositiveIntegerField(default=0)
    # Units held by PENDING (placed but not-yet-confirmed) orders. Physical
    # `stock` is only decremented when an admin confirms the order. Until then a
    # reservation reduces what NEW customers can order without touching stock.
    reserved = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    @property
    def available(self):
        """Units a new customer can actually order right now."""
        return max(self.stock - self.reserved, 0)

    def save(self, *args, **kwargs):
        # _committed is False only on a freshly-assigned upload; existing S3 files are skipped.
        if self.image and not getattr(self.image, "_committed", True):
            self.image = _compress_to_jpeg(self.image)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - ₹{self.price}"


class StockMovement(models.Model):
    """
    Append-only ledger of every change to a product's stock.

    One row is written for each stock mutation (sale, return, stock-take
    upload, bulk edit, manual adjustment). `delta` is signed (negative for a
    decrement) and `balance_after` records the resulting stock so the history
    is self-explanatory even if the product row changes later. Rows are never
    updated or deleted in normal operation.
    """

    class Reason(models.TextChoices):
        STOCKTAKE = "STOCKTAKE", "Stock-take upload"
        BULK_EDIT = "BULK_EDIT", "Bulk edit"
        SALE = "SALE", "Sale"
        RETURN = "RETURN", "Return / restock"
        ADJUST = "ADJUST", "Manual adjustment"

    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="movements"
    )
    delta = models.IntegerField(help_text="Signed change; negative = decrement.")
    balance_after = models.PositiveIntegerField()
    reason = models.CharField(max_length=16, choices=Reason.choices)
    # Free-form pointer to the source of the change, e.g. "order:12", "invoice:5".
    reference = models.CharField(max_length=64, blank=True, default="")
    note = models.CharField(max_length=255, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["product", "-created_at"]),
        ]

    def __str__(self):
        sign = "+" if self.delta >= 0 else ""
        return f"{self.product_id}: {sign}{self.delta} -> {self.balance_after} ({self.reason})"
