import pytest
from app.infrastructure.s3_repository import S3Repository


@pytest.mark.integration
def test_fakecloud_s3_bucket_and_object_roundtrip():
    repo = S3Repository()
    repo.ensure_bucket()
    repo.client.put_object(
        Bucket=repo.settings.s3_bucket,
        Key="integration-test/hello.txt",
        Body=b"hello fakecloud",
        ContentType="text/plain",
    )
    response = repo.client.get_object(
        Bucket=repo.settings.s3_bucket,
        Key="integration-test/hello.txt",
    )
    assert response["Body"].read() == b"hello fakecloud"
