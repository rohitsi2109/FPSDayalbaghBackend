import os
import django
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FPSDayalbaghBackend.settings')
django.setup()

from products.models import Product

def analyze():
    dupes = Product.objects.values('name').annotate(count=Count('id')).filter(count__gt=1)
    print(f"Found {len(dupes)} duplicate names.\n")
    
    for d in dupes:
        name = d['name']
        prods = Product.objects.filter(name=name).order_by('id')
        print(f"--- Product: {name} ({len(prods)} entries) ---")
        for p in prods:
            has_image = bool(p.image)
            print(f"  ID: {p.id} | Cat: {p.category.name if p.category else 'None'} | Stock: {p.stock} | Price: {p.price} | Image: {has_image}")
        print()

if __name__ == "__main__":
    analyze()
