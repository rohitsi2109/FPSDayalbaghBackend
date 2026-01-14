import os
import boto3
from dotenv import load_dotenv
from botocore.config import Config

load_dotenv(override=True)

def debug_s3_permissions():
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=os.environ.get('AWS_S3_ENDPOINT_URL'),
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_S3_REGION_NAME'),
            config=Config(signature_version='s3v4') # Supabase often prefers s3v4
        )
        
        bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'product')
        file_name = 'test_final_connection.txt' # File we uploaded earlier
        
        print(f"Checking HeadObject for '{file_name}' in bucket '{bucket_name}'...")
        response = s3.head_object(Bucket=bucket_name, Key=file_name)
        print("HeadObject successful!")
        print(f"Metadata: {response.get('Metadata')}")
        
    except Exception as e:
        print(f"Error during HeadObject test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_s3_permissions()
