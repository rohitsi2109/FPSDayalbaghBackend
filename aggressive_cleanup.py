import os
import django
import re
from django.db.models import Count
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FPSDayalbaghBackend.settings')
django.setup()

from products.models import Product

def normalize_name(name):
    if not name:
        return ""
    # Lowercase and remove all non-alphanumeric characters
    return re.sub(r'[^a-z0-9]', '', name.lower())

def cleanup():
    # Fetch all products and group by AGGRESSIVE normalized name
    all_prods = Product.objects.all().select_related('category')
    groups = {}
    
    for p in all_prods:
        key = normalize_name(p.name)
        if key not in groups:
            groups[key] = []
        groups[key].append(p)
    
    dupe_groups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Found {len(dupe_groups)} groups of duplicates (aggressive normalization).\n")
    
    total_deleted = 0
    total_transferred = 0
    
    for norm_name, prods in dupe_groups.items():
        # Sort: Has Image > Has Category > Highest ID
        prods.sort(key=lambda p: (1 if p.image else 0, 1 if p.category_id else 0, p.id), reverse=True)
        
        keep = prods[0]
        to_delete = prods[1:]
        
        print(f"Group: '{norm_name}'")
        print(f"  KEEP: ID {keep.id} (Name: '{keep.name}', Cat: {keep.category_id}, Image: {bool(keep.image)})")
        
        for p in to_delete:
            # Transfer relations
            for rel in p._meta.related_objects:
                accessor = rel.get_accessor_name()
                try:
                    related_qs = getattr(p, accessor).all()
                    if related_qs.exists():
                        print(f"    Transferring {related_qs.count()} {rel.related_model.__name__} items to ID {keep.id}")
                        related_qs.update(**{rel.field.name: keep})
                        total_transferred += related_qs.count()
                except Exception as e:
                    print(f"    Error transferring {accessor}: {e}")
            
            print(f"  DELETE: ID {p.id} (Name: '{p.name}')")
            p.delete()
            total_deleted += 1
        print()

    print(f"Cleanup finished. Deleted: {total_deleted}, Transferred relations: {total_transferred}")

if __name__ == "__main__":
    with transaction.atomic():
        cleanup()
