"""Cloudflare R2 StorageClient — the only R2/boto3-aware module.

R2 is S3-compatible, so this is a thin boto3 client pointed at the account
endpoint. Public objects are served from a configured base URL (an r2.dev domain
or a custom domain), so url() is a simple join rather than a signed URL.
"""

from typing import BinaryIO

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from core.storage.base import StorageError


class R2Storage:
    """StorageClient backed by a Cloudflare R2 bucket."""

    def __init__(
        self,
        *,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket: str,
        public_base_url: str,
    ) -> None:
        self._bucket = bucket
        self._public_base_url = public_base_url.rstrip("/")
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    def upload(self, file: BinaryIO, *, key: str, content_type: str) -> str:
        try:
            self._client.upload_fileobj(
                file, self._bucket, key, ExtraArgs={"ContentType": content_type}
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"R2 upload failed for {key!r}: {exc}") from exc
        return key

    def download(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()
        except self._client.exceptions.NoSuchKey as exc:
            raise KeyError(key) from exc
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"R2 download failed for {key!r}: {exc}") from exc

    def url(self, key: str) -> str:
        return f"{self._public_base_url}/{key}"

    def delete(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"R2 delete failed for {key!r}: {exc}") from exc

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False
