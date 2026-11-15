"""File storage: S3 when configured, the local disk otherwise.

Every large file this application handles -- uploaded dataset files, the
persisted model artefact, generated referral-packet and visit-prep PDFs --
goes through this module and nowhere else, so whichever ticket writes that
feature never constructs its own S3 client and the backend can be swapped
without touching a caller.

``S3_BUCKET`` set: objects live in that bucket, in ``AWS_REGION``. boto3 reads
its credentials from the environment/instance role automatically; this module
never passes keys, a profile or an endpoint, so the same code runs unmodified
from a sandbox with short-lived credentials to the deployed container with an
instance role.

``S3_BUCKET`` unset (a fresh clone, the unit-test run): objects live under
``MEDIA_ROOT``, a directory that defaults to a folder beside this package so
`pip install -r requirements.txt` is enough to run with nothing else
configured. In production the platform sets ``MEDIA_ROOT`` to a directory that
survives redeploys whenever the deployment uses disk storage instead of S3.

Never a public object: a read is always either a short-lived presigned URL
(S3) or a path this application's own route would have to resolve (disk) --
never a public bucket ACL and never a path outside ``MEDIA_ROOT``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Beside the `app` package, not inside it, so the directory a stray local run
# creates is never mistaken for application code.
DEFAULT_MEDIA_ROOT = str(Path(__file__).resolve().parent.parent / "media")


def _s3_bucket() -> str | None:
    return os.getenv("S3_BUCKET") or None


def _aws_region() -> str | None:
    return os.getenv("AWS_REGION") or None


def _media_root() -> Path:
    root = Path(os.getenv("MEDIA_ROOT", DEFAULT_MEDIA_ROOT))
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_path(key: str) -> Path:
    """`key` resolved under MEDIA_ROOT, refusing to escape it (e.g. "../../etc/passwd")."""
    root = _media_root().resolve()
    candidate = (root / key).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"storage key escapes MEDIA_ROOT: {key!r}")
    return candidate


def _s3_client():
    import boto3  # imported lazily: never required when S3_BUCKET is unset

    return boto3.client("s3", region_name=_aws_region())


@dataclass(frozen=True)
class StoredFile:
    """Where a save landed, in a shape both backends can return."""

    key: str
    backend: str  # "s3" | "disk"


def save_bytes(key: str, data: bytes, content_type: str | None = None) -> StoredFile:
    """Write `data` under `key` (a relative path, e.g. "packets/<id>.pdf")."""
    bucket = _s3_bucket()
    if bucket:
        extra = {"ContentType": content_type} if content_type else {}
        _s3_client().put_object(Bucket=bucket, Key=key, Body=data, **extra)
        return StoredFile(key=key, backend="s3")
    path = _safe_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return StoredFile(key=key, backend="disk")


def read_bytes(key: str) -> bytes:
    """The bytes stored under `key`, from whichever backend holds it."""
    bucket = _s3_bucket()
    if bucket:
        response = _s3_client().get_object(Bucket=bucket, Key=key)
        return response["Body"].read()
    return _safe_path(key).read_bytes()


def delete(key: str) -> None:
    """Remove `key`. Quiet when it never existed -- callers retry safely."""
    bucket = _s3_bucket()
    if bucket:
        _s3_client().delete_object(Bucket=bucket, Key=key)
        return
    _safe_path(key).unlink(missing_ok=True)


def url_for(key: str, expires_in: int = 3600) -> str:
    """A short-lived link to `key`.

    S3: a presigned GET URL that expires in `expires_in` seconds -- the object
    itself is never made public. Disk: a path under this application's own
    `/media/` route; serving that route is the job of whichever ticket first
    needs to hand a file to a browser (e.g. the PDF export), not this module.
    """
    bucket = _s3_bucket()
    if bucket:
        return _s3_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    return f"/media/{key}"
