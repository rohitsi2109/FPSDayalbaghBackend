from io import BytesIO

from django.core.files.base import ContentFile
from django.db import models


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
    thumbnail = models.ImageField(upload_to='products/thumbs/', blank=True, null=True)

    THUMB_MAX = (300, 300)
    THUMB_QUALITY = 82

    def __str__(self):
        return f"{self.name} - ₹{self.price}"

    def save(self, *args, **kwargs):
        old_image_name = None
        if self.pk:
            old_image_name = (
                type(self).objects
                .filter(pk=self.pk)
                .values_list('image', flat=True)
                .first()
            )

        super().save(*args, **kwargs)

        new_image_name = self.image.name if self.image else None
        image_changed = old_image_name != new_image_name

        if self.image and (image_changed or not self.thumbnail):
            self._regenerate_thumbnail()
        elif not self.image and self.thumbnail:
            self.thumbnail.delete(save=False)
            super().save(update_fields=['thumbnail'])

    def _regenerate_thumbnail(self):
        try:
            from PIL import Image as PILImage
        except ImportError:
            return

        try:
            self.image.open('rb')
            with PILImage.open(self.image.file) as img:
                if img.mode in ('RGBA', 'LA'):
                    bg = PILImage.new('RGB', img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[-1])
                    img = bg
                elif img.mode == 'P':
                    img = img.convert('RGBA')
                    bg = PILImage.new('RGB', img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[-1])
                    img = bg
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                img.thumbnail(self.THUMB_MAX, PILImage.Resampling.LANCZOS)

                buf = BytesIO()
                img.save(buf, format='JPEG', quality=self.THUMB_QUALITY, optimize=True)
                buf.seek(0)

                base = self.image.name.rsplit('/', 1)[-1].rsplit('.', 1)[0]
                self.thumbnail.save(f'{base}.jpg', ContentFile(buf.getvalue()), save=False)
        except Exception:
            return
        finally:
            try:
                self.image.close()
            except Exception:
                pass

        super().save(update_fields=['thumbnail'])
