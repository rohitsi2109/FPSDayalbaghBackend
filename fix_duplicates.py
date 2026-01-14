import os
import django
from django.db.models import Count
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FPSDayalbaghBackend.settings')
django.setup()

from products.models import Product

def cleanup():
    # Fetch all products and group by normalized name ONLY
    all_prods = Product.objects.all().select_related('category')
    groups = {}
    
    for p in all_prods:
        key = p.name.lower().strip()
        if key not in groups:
            groups[key] = []
        groups[key].append(p)
    
    dupe_groups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Found {len(dupe_groups)} groups of duplicates (name only).\n")
    
    total_deleted = 0
    total_transferred = 0
    
    for name, prods in dupe_groups.items():
        # Sort: Has Image > Has Category > Highest ID
        prods.sort(key=lambda p: (1 if p.image else 0, 1 if p.category_id else 0, p.id), reverse=True)
        
        keep = prods[0]
        to_delete = prods[1:]
        
        print(f"Group: '{name}'")
        print(f"  KEEP: ID {keep.id} (Cat: {keep.category_id}, Image: {bool(keep.image)})")
        
        for p in to_delete:
            # Check for related order items (assuming the relation is named 'orderitem' or similar)
            # We can use the product's reverse relation. In Django, if not specified, it's <model>_set.
            # Based on the error, it's 'OrderItem'. Let's try to update the foreign keys.
            
            # Since I don't know the exact related names, I'll use a generic approach to find relations
            for rel in p._meta.related_objects:
                accessor = rel.get_accessor_name()
                related_qs = getattr(p, accessor).all()
                if related_qs.exists():
                    print(f"    Transferring {related_qs.count()} {rel.related_model.__name__} items to ID {keep.id}")
                    related_qs.update(**{rel.field.name: keep})
                    total_transferred += related_qs.count()
            
            print(f"  DELETE: ID {p.id}")
            p.delete()
            total_deleted += 1
        print()

    print(f"Cleanup finished. Deleted: {total_deleted}, Transferred relations: {total_transferred}")

if __name__ == "__main__":
    with transaction.atomic():
        cleanup()
