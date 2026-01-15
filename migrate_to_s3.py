import os
import boto3
from dotenv import load_dotenv

load_dotenv(override=True)

def migrate():
    s3 = boto3.client(
        's3',
        endpoint_url=os.environ.get('AWS_S3_ENDPOINT_URL'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_S3_REGION_NAME'),
    )
    
    bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'product')
    local_media_root = os.path.join('media', 'products')
    
    if not os.path.exists(local_media_root):
        print(f"Local directory {local_media_root} not found.")
        return

    files = [f for f in os.listdir(local_media_root) if os.path.isfile(os.path.join(local_media_root, f))]
    total = len(files)
    print(f"Found {total} files in {local_media_root}. Starting migration to bucket '{bucket_name}'...")

    for i, filename in enumerate(files, 1):
        local_path = os.path.join(local_media_root, filename)
        s3_key = f"products/{filename}"
        
        try:
            # Check if exists to avoid re-uploading (optional)
            # We'll just upload for now to be sure.
            with open(local_path, 'rb') as f:
                s3.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=f,
                    # Supabase doesn't strictly need ACL if bucket is public, 
                    # but we can set it to be safe if required.
                    # ACL='public-read' 
                )
            print(f"[{i}/{total}] Uploaded: {s3_key}")
        except Exception as e:
            print(f"[{i}/{total}] Failed to upload {filename}: {e}")

    print("Migration complete!")

if __name__ == "__main__":
    migrate()
