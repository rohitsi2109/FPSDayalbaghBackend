"""
Copy every object from the existing Supabase Storage bucket to your new AWS
S3 bucket. Idempotent: skips keys that already exist on the destination,
so re-running is safe.

Setup
-----
Add a `.env.migration` file (gitignored) next to this script with BOTH sets
of credentials. SRC_* are your current Supabase ones; DST_* are AWS:

    SRC_AWS_ACCESS_KEY_ID=...                       # Supabase storage key
    SRC_AWS_SECRET_ACCESS_KEY=...                   # Supabase storage secret
    SRC_AWS_STORAGE_BUCKET_NAME=product
    SRC_AWS_S3_ENDPOINT_URL=https://autsahhilzzsiaowhisk.storage.supabase.co/storage/v1/s3
    SRC_AWS_S3_REGION_NAME=ap-south-1

    DST_AWS_ACCESS_KEY_ID=...                       # AWS IAM key
    DST_AWS_SECRET_ACCESS_KEY=...                   # AWS IAM secret
    DST_AWS_STORAGE_BUCKET_NAME=fairprice-211125406099-ap-southeast-2-an
    DST_AWS_S3_REGION_NAME=ap-southeast-2

Usage
-----
    # dry run — list what would be copied
    python migrate_supabase_to_aws.py

    # actually copy
    python migrate_supabase_to_aws.py --apply

    # re-copy even objects that already exist on AWS
    python migrate_supabase_to_aws.py --apply --force

    # only copy keys under a prefix
    python migrate_supabase_to_aws.py --apply --prefix products/
"""

import argparse
import os
import sys

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv


CACHE_CONTROL = "public, max-age=31536000, immutable"


def _env(key, required=True):
    val = os.environ.get(key, "").strip()
    if required and not val:
        sys.exit(f"missing env var: {key}")
    return val or None


def make_client(prefix, addressing_style):
    return boto3.client(
        "s3",
        aws_access_key_id=_env(f"{prefix}AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=_env(f"{prefix}AWS_SECRET_ACCESS_KEY"),
        region_name=_env(f"{prefix}AWS_S3_REGION_NAME"),
        endpoint_url=os.environ.get(f"{prefix}AWS_S3_ENDPOINT_URL") or None,
        config=Config(signature_version="s3v4", s3={"addressing_style": addressing_style}),
    )


def list_all_keys(s3, bucket, prefix=""):
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            yield obj["Key"], obj.get("Size", 0)


def exists_on_dst(dst, bucket, key):
    try:
        dst.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise


def guess_content_type(key):
    k = key.lower()
    if k.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if k.endswith(".png"):
        return "image/png"
    if k.endswith(".webp"):
        return "image/webp"
    if k.endswith(".gif"):
        return "image/gif"
    if k.endswith(".pdf"):
        return "application/pdf"
    return "application/octet-stream"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true", help="Actually copy (default: dry-run)")
    p.add_argument("--force", action="store_true", help="Re-copy even if dst already has the key")
    p.add_argument("--prefix", default="", help="Only copy keys under this prefix")
    args = p.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(here, ".env.migration"), override=True)

    src_bucket = _env("SRC_AWS_STORAGE_BUCKET_NAME")
    dst_bucket = _env("DST_AWS_STORAGE_BUCKET_NAME")

    # Supabase requires path-style; AWS prefers virtual-hosted–style.
    src = make_client("SRC_", addressing_style="path")
    dst = make_client("DST_", addressing_style="virtual")

    print(f"src: {src_bucket}  ({os.environ.get('SRC_AWS_S3_ENDPOINT_URL') or 'AWS'})")
    print(f"dst: {dst_bucket}  ({os.environ.get('DST_AWS_S3_ENDPOINT_URL') or 'AWS'})")
    print(f"prefix: {args.prefix or '<all>'}")
    print(f"mode:   {'APPLY' if args.apply else 'dry-run'}{' (force)' if args.force else ''}")
    print()

    copied = 0
    skipped = 0
    failed = 0
    bytes_copied = 0

    for key, size in list_all_keys(src, src_bucket, prefix=args.prefix):
        if not args.force and exists_on_dst(dst, dst_bucket, key):
            skipped += 1
            print(f"  skip  {key}  ({size} B — already on dst)")
            continue

        if not args.apply:
            print(f"  WOULD COPY  {key}  ({size} B)")
            continue

        try:
            obj = src.get_object(Bucket=src_bucket, Key=key)
            body = obj["Body"].read()
            dst.put_object(
                Bucket=dst_bucket,
                Key=key,
                Body=body,
                ContentType=obj.get("ContentType") or guess_content_type(key),
                CacheControl=CACHE_CONTROL,
            )
            copied += 1
            bytes_copied += len(body)
            print(f"  ok    {key}  ({len(body)} B)")
        except Exception as exc:
            failed += 1
            print(f"  ERR   {key}  {exc}")

    print()
    print(
        f"done. copied={copied} skipped={skipped} failed={failed} "
        f"bytes={bytes_copied:,}"
    )
    if not args.apply:
        print("dry-run only — re-run with --apply to actually copy.")


if __name__ == "__main__":
    main()
