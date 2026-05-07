import io

from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models


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
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def save(self, *args, **kwargs):
        # _committed is False only on a freshly-assigned upload; existing S3 files are skipped.
        if self.image and not getattr(self.image, "_committed", True):
            self.image = _compress_to_jpeg(self.image)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - ₹{self.price}"
