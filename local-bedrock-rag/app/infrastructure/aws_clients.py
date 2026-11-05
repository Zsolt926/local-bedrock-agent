import boto3
from botocore.config import Config
from app.core.config import get_settings


def _client(service_name: str, *, s3_path_style: bool = False):
    settings = get_settings()
    config_kwargs = {
        "retries": {"max_attempts": 1, "mode": "standard"},
    }
    if s3_path_style:
        config_kwargs["s3"] = {"addressing_style": settings.s3_addressing_style}
    kwargs = {
        "service_name": service_name,
        "region_name": settings.aws_region,
        "config": Config(**config_kwargs),
    }
    if settings.use_fakecloud:
        kwargs.update({
            "endpoint_url": settings.fakecloud_endpoint_url,
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
        })
    # In real-AWS mode boto3 uses its normal credential provider chain.
    return boto3.client(**kwargs)


def s3_client():
    return _client("s3", s3_path_style=True)


def bedrock_agent_client():
    return _client("bedrock-agent")


def bedrock_agent_runtime_client():
    return _client("bedrock-agent-runtime")


def bedrock_runtime_client():
    return _client("bedrock-runtime")
