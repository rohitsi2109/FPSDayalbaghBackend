import os
import boto3
from dotenv import load_dotenv

load_dotenv(override=True)

def upload_apk():
    s3 = boto3.client(
        's3',
        endpoint_url=os.environ.get('AWS_S3_ENDPOINT_URL'),
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_S3_REGION_NAME'),
    )
    
    bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'product')
    local_path = os.path.join('media', 'FPS.apk')
    s3_key = 'FPS.apk'
    
    if not os.path.exists(local_path):
        print(f"Local file {local_path} not found.")
        return

    try:
        print(f"Uploading {local_path} to bucket '{bucket_name}' as '{s3_key}'...")
        with open(local_path, 'rb') as f:
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=f,
                ContentType='application/vnd.android.package-archive'
            )
        print("Upload complete!")
        print(f"URL: https://autsahhilzzsiaowhisk.supabase.co/storage/v1/object/public/product/{s3_key}")
    except Exception as e:
        print(f"Failed to upload: {e}")

if __name__ == "__main__":
    upload_apk()
