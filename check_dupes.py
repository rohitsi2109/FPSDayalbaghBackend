import os
import django
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FPSDayalbaghBackend.settings')
django.setup()

from products.models import Product

dupes = Product.objects.values('name').annotate(count=Count('id')).filter(count__gt=1)
print(f"Duplicate Names found: {len(dupes)}")
for d in dupes:
    print(f"{d['name']}: {d['count']}")
