import os
import django
from dotenv import load_dotenv
load_dotenv(override=True)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FPSDayalbaghBackend.settings')
django.setup()

from products.models import Product

def check_product(pid):
    try:
        p = Product.objects.get(id=pid)
        print(f"Product ID: {p.id}")
        print(f"Name: {p.name}")
        print(f"Image Name: {p.image.name if p.image else 'None'}")
        if p.image:
            from django.core.files.storage import default_storage
            print(f"Image Storage Class: {p.image.storage.__class__}")
            print(f"Exists in storage? {p.image.storage.exists(p.image.name)}")
            print(f"URL: {p.image.url}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_product(2054)
