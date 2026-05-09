"""
Download every object from your current Supabase Storage bucket to a local
folder. Idempotent: re-running only fetches keys that aren't already on disk
(unless you pass --force).

Read `.env` for credentials. Right now your `.env` AWS_* vars point at
Supabase, so this script needs no extra config — just run it.

Output goes to ./supabase_backup/<key> (preserving folder structure inside
the bucket, e.g. supabase_backup/products/foo.jpg).

Usage
-----
    python pull_supabase_backup.py                  # dry run / list
    python pull_supabase_backup.py --apply          # actually download
    python pull_supabase_backup.py --apply --force  # redownload everything
    python pull_supabase_backup.py --apply --prefix products/
"""

import argparse
import os
import sys

import boto3
from botocore.config import Config
from dotenv import load_dotenv


def _env(key, required=True):
    val = (os.environ.get(key) or "").strip()
    if required and not val:
        sys.exit(f"missing env var: {key}")
    return val or None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true", help="Actually download (default: dry-run)")
    p.add_argument("--force", action="store_true", help="Redownload even if file exists locally")
    p.add_argument("--prefix", default="", help="Only pull keys under this prefix")
    p.add_argument("--out", default="supabase_backup", help="Output directory (default: supabase_backup)")
    args = p.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(here, ".env"), override=True)

    bucket = _env("AWS_STORAGE_BUCKET_NAME")
    endpoint = _env("AWS_S3_ENDPOINT_URL")
    region = _env("AWS_S3_REGION_NAME")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=_env("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=_env("AWS_SECRET_ACCESS_KEY"),
        region_name=region,
        endpoint_url=endpoint,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )

    out_root = os.path.join(here, args.out)
    os.makedirs(out_root, exist_ok=True)

    print(f"bucket:   {bucket}")
    print(f"endpoint: {endpoint}")
    print(f"region:   {region}")
    print(f"out:      {out_root}")
    print(f"prefix:   {args.prefix or '<all>'}")
    print(f"mode:     {'APPLY' if args.apply else 'dry-run'}{' (force)' if args.force else ''}")
    print()

    total = 0
    skipped = 0
    downloaded = 0
    failed = 0
    bytes_downloaded = 0

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=args.prefix):
        for obj in page.get("Contents", []) or []:
            key = obj["Key"]
            size = obj.get("Size", 0)
            total += 1

            local_path = os.path.join(out_root, *key.split("/"))
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            if not args.force and os.path.exists(local_path) and os.path.getsize(local_path) == size:
                skipped += 1
                print(f"  skip  {key}  ({size} B — already local)")
                continue

            if not args.apply:
                print(f"  WOULD DOWNLOAD  {key}  ({size} B)")
                continue

            try:
                s3.download_file(bucket, key, local_path)
                downloaded += 1
                bytes_downloaded += size
                print(f"  ok    {key}  ({size} B)")
            except Exception as exc:
                failed += 1
                print(f"  ERR   {key}  {exc}")

    print()
    print(
        f"done. total={total} downloaded={downloaded} skipped={skipped} "
        f"failed={failed} bytes={bytes_downloaded:,}"
    )
    if not args.apply and total:
        print("dry-run only — re-run with --apply to actually download.")


if __name__ == "__main__":
    main()
