"""
Upload everything in ./supabase_backup/ to your AWS S3 bucket. Idempotent:
skips keys that already exist on AWS, so re-running is safe.

Setup
-----
Create `.env.aws` (gitignored) next to this script with AWS-only creds:

    DST_AWS_ACCESS_KEY_ID=...
    DST_AWS_SECRET_ACCESS_KEY=...
    DST_AWS_STORAGE_BUCKET_NAME=fairprice-211125406099-ap-southeast-2-an
    DST_AWS_S3_REGION_NAME=ap-southeast-2

Your existing `.env` (Supabase) stays untouched — production keeps working.

Usage
-----
    python push_backup_to_aws.py                       # dry run
    python push_backup_to_aws.py --apply               # actually upload
    python push_backup_to_aws.py --apply --force       # re-upload everything
    python push_backup_to_aws.py --apply --prefix products/
"""

import argparse
import os
import sys

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv


CACHE_CONTROL = "public, max-age=31536000, immutable"
BACKUP_DIR_DEFAULT = "supabase_backup"


def _env(key, required=True):
    val = (os.environ.get(key) or "").strip()
    if required and not val:
        sys.exit(f"missing env var: {key}")
    return val or None


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
    if k.endswith(".avif"):
        return "image/avif"
    if k.endswith(".pdf"):
        return "application/pdf"
    return "application/octet-stream"


_warned_403 = False


def exists_on_dst(s3, bucket, key, expected_size):
    global _warned_403
    try:
        head = s3.head_object(Bucket=bucket, Key=key)
        return head.get("ContentLength") == expected_size
    except ClientError as e:
        code = e.response["Error"]["Code"]
        status = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if code in {"404", "NoSuchKey", "NotFound"} or status == 404:
            return False
        if code in {"403", "Forbidden", "AccessDenied"} or status == 403:
            # AWS returns 403 (not 404) on HeadObject when the caller lacks
            # s3:ListBucket on the bucket. Treat as "not present" so the upload
            # is attempted — if credentials are truly broken, PutObject will
            # surface a clean 403 with a useful message.
            if not _warned_403:
                _warned_403 = True
                print(
                    "  note: HeadObject returned 403 — the IAM user likely lacks "
                    "s3:ListBucket on the bucket. Proceeding (uploads will still work)."
                )
            return False
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true", help="Actually upload (default: dry-run)")
    p.add_argument("--force", action="store_true", help="Re-upload even if dst already has the key")
    p.add_argument("--prefix", default="", help="Only upload keys under this prefix")
    p.add_argument("--src", default=BACKUP_DIR_DEFAULT, help=f"Local source dir (default: {BACKUP_DIR_DEFAULT})")
    args = p.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(here, ".env.aws"), override=True)

    src_root = os.path.join(here, args.src)
    if not os.path.isdir(src_root):
        sys.exit(f"source directory not found: {src_root}")

    bucket = _env("DST_AWS_STORAGE_BUCKET_NAME")
    region = _env("DST_AWS_S3_REGION_NAME")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=_env("DST_AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=_env("DST_AWS_SECRET_ACCESS_KEY"),
        region_name=region,
        config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    )

    print(f"src:    {src_root}")
    print(f"dst:    s3://{bucket}  ({region})")
    print(f"prefix: {args.prefix or '<all>'}")
    print(f"mode:   {'APPLY' if args.apply else 'dry-run'}{' (force)' if args.force else ''}")
    print()

    uploaded = 0
    skipped = 0
    failed = 0
    bytes_uploaded = 0

    for dirpath, _, filenames in os.walk(src_root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            # build the S3 key relative to the backup root, using forward slashes
            rel = os.path.relpath(full, src_root).replace(os.sep, "/")
            if args.prefix and not rel.startswith(args.prefix):
                continue

            size = os.path.getsize(full)

            if not args.force and exists_on_dst(s3, bucket, rel, size):
                skipped += 1
                print(f"  skip  {rel}  ({size} B — already on dst)")
                continue

            if not args.apply:
                print(f"  WOULD UPLOAD  {rel}  ({size} B)")
                continue

            try:
                with open(full, "rb") as fh:
                    s3.put_object(
                        Bucket=bucket,
                        Key=rel,
                        Body=fh,
                        ContentType=guess_content_type(rel),
                        CacheControl=CACHE_CONTROL,
                    )
                uploaded += 1
                bytes_uploaded += size
                print(f"  ok    {rel}  ({size} B)")
            except Exception as exc:
                failed += 1
                print(f"  ERR   {rel}  {exc}")

    print()
    print(
        f"done. uploaded={uploaded} skipped={skipped} failed={failed} "
        f"bytes={bytes_uploaded:,}"
    )
    if not args.apply and (uploaded + skipped + failed) == 0 and not args.prefix:
        # nothing matched at all — give a hint
        print("(no files found under src)")


if __name__ == "__main__":
    main()
