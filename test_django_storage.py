import os
import django
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from dotenv import load_dotenv
load_dotenv(override=True)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FPSDayalbaghBackend.settings')
django.setup()

def test_storage():
    try:
        from django.conf import settings
        print(f"Storage class: {default_storage.__class__}")
        print(f"Bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
        
        file_name = 'products/test_django_storage.txt'
        content = 'Testing S3Boto3Storage via Django in a subfolder.'
        
        if default_storage.exists(file_name):
            print(f"File {file_name} exists.")
        else:
            print(f"Saving {file_name}...")
            path = default_storage.save(file_name, ContentFile(content))
            print(f"Saved to: {path}")
            
        url = default_storage.url(file_name)
        print(f"Generated URL: {url}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_storage()
