import os
import django
import requests
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FPSDayalbaghBackend.settings')
django.setup()

from products.models import Product

import tempfile

def attach_image_from_url(product_id, url):
    try:
        product = Product.objects.get(id=product_id)
        print(f"Attaching image to Product: {product.name} (ID: {product_id}) from URL: {url}")
        
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            # Create a named temp file manually for better Windows compatibility
            suffix = os.path.splitext(os.path.basename(url).split('?')[0])[1] or '.jpg'
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as img_temp:
                img_temp.write(response.content)
                img_temp_path = img_temp.name
            
            try:
                with open(img_temp_path, 'rb') as f:
                    filename = os.path.basename(img_temp_path)
                    product.image.save(filename, File(f), save=True)
                print(f"Successfully attached image to {product.name}")
                return True
            finally:
                if os.path.exists(img_temp_path):
                    os.remove(img_temp_path)
        else:
            print(f"Failed to download image. Status code: {response.status_code}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error attaching image: {e}")
    return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python attach_image.py <product_id> <url>")
    else:
        attach_image_from_url(int(sys.argv[1]), sys.argv[2])
