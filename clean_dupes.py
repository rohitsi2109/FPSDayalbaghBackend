import os
import django
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FPSDayalbaghBackend.settings')
django.setup()

from products.models import Product

dupes = Product.objects.values('name').annotate(count=Count('id')).filter(count__gt=1)
print(f"Cleaning {len(dupes)} duplicates...")

for d in dupes:
    name = d['name']
    products = list(Product.objects.filter(name=name).order_by('id'))
    # Keep the last one, delete others
    to_delete = products[:-1]
    keep = products[-1]
    print(f"Keeping {keep.id}, deleting {[p.id for p in to_delete]}")
    for p in to_delete:
        p.delete()

print("Cleanup complete.")
