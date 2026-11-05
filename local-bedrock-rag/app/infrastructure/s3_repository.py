import json
import mimetypes
from pathlib import Path
from botocore.exceptions import ClientError
from app.core.config import get_settings
from app.infrastructure.aws_clients import s3_client


class S3Repository:
    def __init__(self):
        self.settings = get_settings()
        self.client = s3_client()

    @property
    def bucket_arn(self) -> str:
        return f"arn:aws:s3:::{self.settings.s3_bucket}"

    def ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.settings.s3_bucket)
            return
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code not in {"404", "NoSuchBucket", "NotFound"}:
                raise

        kwargs = {"Bucket": self.settings.s3_bucket}
        if self.settings.aws_region != "us-east-1":
            kwargs["CreateBucketConfiguration"] = {
                "LocationConstraint": self.settings.aws_region
            }
        self.client.create_bucket(**kwargs)

    def upload_file(self, path: Path, metadata: dict | None = None) -> dict:
        self.ensure_bucket()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        key = f"{self.settings.s3_document_prefix}{path.name}"
        self.client.upload_file(
            str(path),
            self.settings.s3_bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )

        # Bedrock S3 data sources use <document-key>.metadata.json sidecar files.
        sidecar = path.with_name(path.name + ".metadata.json")
        if metadata is None and sidecar.exists():
            metadata = json.loads(sidecar.read_text(encoding="utf-8"))
        if metadata is not None:
            self.client.put_object(
                Bucket=self.settings.s3_bucket,
                Key=key + ".metadata.json",
                Body=json.dumps(metadata, ensure_ascii=False).encode("utf-8"),
                ContentType="application/json",
            )
        return {
            "bucket": self.settings.s3_bucket,
            "key": key,
            "size_bytes": path.stat().st_size,
            "content_type": content_type,
            "metadata_uploaded": metadata is not None,
        }

    def upload_bytes(
        self, filename: str, content: bytes, content_type: str,
        metadata: dict | None = None,
    ) -> dict:
        self.ensure_bucket()
        key = f"{self.settings.s3_document_prefix}{Path(filename).name}"
        self.client.put_object(
            Bucket=self.settings.s3_bucket,
            Key=key,
            Body=content,
            ContentType=content_type or "application/octet-stream",
        )
        if metadata is not None:
            self.client.put_object(
                Bucket=self.settings.s3_bucket,
                Key=key + ".metadata.json",
                Body=json.dumps(metadata).encode("utf-8"),
                ContentType="application/json",
            )
        return {
            "bucket": self.settings.s3_bucket,
            "key": key,
            "size_bytes": len(content),
            "content_type": content_type,
            "metadata_uploaded": metadata is not None,
        }

    def list_objects(self, prefix: str | None = None) -> list[dict]:
        self.ensure_bucket()
        paginator = self.client.get_paginator("list_objects_v2")
        results = []
        for page in paginator.paginate(
            Bucket=self.settings.s3_bucket,
            Prefix=prefix or self.settings.s3_document_prefix,
        ):
            for item in page.get("Contents", []):
                results.append({
                    "key": item["Key"],
                    "size": item["Size"],
                    "last_modified": item["LastModified"].isoformat(),
                })
        return results
