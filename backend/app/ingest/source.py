"""Opening one file of a dataset drop, from S3 or from the local media root.

The ingest is pointed at a location, not at a single file: `s3://bucket/prefix`
when the drop lives in the project's bucket (the deployed path, where
`S3_BUCKET` is set) or a plain directory path under `MEDIA_ROOT` otherwise --
the same two backends `app.storage` chooses between, and the same credentials
story: boto3 reads them itself, this module never passes keys or an endpoint.

A file is handed back as a byte stream rather than as bytes, so pandas can
read it in chunks and a 572k-row events.csv never has to fit in memory.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO


def _owner_guard() -> dict[str, str]:
    """`ExpectedBucketOwner` when the owning account is configured, else nothing.

    Set `S3_EXPECTED_BUCKET_OWNER` (the AWS account id that owns the bucket) and
    every S3 call fails rather than reading a bucket that changed hands or whose
    name was taken over by another account.
    """
    owner = os.getenv("S3_EXPECTED_BUCKET_OWNER", "").strip()
    return {"ExpectedBucketOwner": owner} if owner else {}


def list_source_files(source_uri: str, prefix: str = "") -> list[str]:
    """The names (relative to the drop) of the files under `prefix` in the drop.

    Used to discover which `fhir/*.ndjson.gz` resource types a drop actually
    contains; an absent directory or prefix is simply an empty list.
    """
    if source_uri.startswith("s3://"):
        bucket, _, base = source_uri[len("s3://") :].partition("/")
        base = base.rstrip("/")
        import boto3  # imported lazily: never needed for a disk drop

        client = boto3.client("s3", region_name=os.getenv("AWS_REGION") or None)
        full_prefix = f"{base}/{prefix}" if base else prefix
        names: list[str] = []
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=full_prefix, **_owner_guard()):
            for item in page.get("Contents", []):
                key = item["Key"]
                relative = key[len(base) + 1 :] if base else key
                if relative:
                    names.append(relative)
        return sorted(names)

    root = Path(source_uri)
    directory = root / prefix if prefix else root
    if not directory.is_dir():
        return []
    return sorted(
        str(path.relative_to(root)).replace(os.sep, "/")
        for path in directory.iterdir()
        if path.is_file()
    )


@contextmanager
def open_source_file(source_uri: str, name: str) -> Iterator[BinaryIO]:
    """A readable byte stream for `name` inside the drop at `source_uri`."""
    if source_uri.startswith("s3://"):
        bucket, _, prefix = source_uri[len("s3://") :].partition("/")
        key = f"{prefix.rstrip('/')}/{name}" if prefix else name
        import boto3  # imported lazily: never needed for a disk drop

        client = boto3.client("s3", region_name=os.getenv("AWS_REGION") or None)
        body = client.get_object(Bucket=bucket, Key=key, **_owner_guard())["Body"]
        try:
            yield body
        finally:
            body.close()
        return

    path = Path(source_uri) / name
    with path.open("rb") as handle:
        yield handle
