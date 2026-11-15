"""Unit tests for `app.storage`: the disk backend for real, S3 with a fake client.

The disk backend needs no fake -- it is real local disk, scoped to a temporary
`MEDIA_ROOT` so a test never leaves a file behind and never touches the
application's own media directory. The S3 backend is never exercised against
a real bucket here (the sandbox's `S3_BUCKET` is unset for this test by
`_isolated_media_root`): `boto3.client` is replaced with a stand-in so the
module's own call shape is verified without a network call.
"""

from unittest.mock import MagicMock, patch

import pytest

from app import storage


@pytest.fixture(autouse=True)
def _isolated_media_root(tmp_path, monkeypatch):
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path))
    monkeypatch.delenv("S3_BUCKET", raising=False)


def test_disk_round_trip():
    saved = storage.save_bytes("reports/example.pdf", b"hello world")
    assert saved.backend == "disk"
    assert storage.read_bytes("reports/example.pdf") == b"hello world"


def test_disk_creates_parent_directories():
    storage.save_bytes("deeply/nested/path/file.txt", b"x")
    assert storage.read_bytes("deeply/nested/path/file.txt") == b"x"


def test_disk_delete_is_quiet_when_nothing_was_there():
    storage.delete("never-existed.txt")  # must not raise


def test_disk_delete_removes_the_file():
    storage.save_bytes("tmp/throwaway.txt", b"x")
    storage.delete("tmp/throwaway.txt")
    with pytest.raises(FileNotFoundError):
        storage.read_bytes("tmp/throwaway.txt")


def test_disk_url_is_a_local_media_path():
    assert storage.url_for("reports/example.pdf") == "/media/reports/example.pdf"


def test_disk_refuses_a_key_that_escapes_media_root():
    with pytest.raises(ValueError):
        storage.save_bytes("../../etc/passwd", b"x")


def test_s3_backend_used_when_bucket_configured(monkeypatch):
    monkeypatch.setenv("S3_BUCKET", "test-bucket")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    fake_client = MagicMock()
    fake_client.generate_presigned_url.return_value = "https://example.test/signed"

    with patch("boto3.client", return_value=fake_client) as make_client:
        saved = storage.save_bytes(
            "artefacts/model.joblib", b"binary", content_type="application/octet-stream"
        )
        assert saved.backend == "s3"
        fake_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="artefacts/model.joblib",
            Body=b"binary",
            ContentType="application/octet-stream",
        )

        assert storage.url_for("artefacts/model.joblib") == "https://example.test/signed"
        fake_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "artefacts/model.joblib"},
            ExpiresIn=3600,
        )

        storage.read_bytes("artefacts/model.joblib")
        fake_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="artefacts/model.joblib"
        )

        storage.delete("artefacts/model.joblib")
        fake_client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="artefacts/model.joblib"
        )

    make_client.assert_called_with("s3", region_name="us-east-1")
