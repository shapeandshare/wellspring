"""S3Sdk maps s3:// URIs onto the S3 API (spec 027 research R4); offline via Stubber."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Iterator
from io import BytesIO

import boto3
import pytest
from botocore.client import BaseClient
from botocore.response import StreamingBody
from botocore.stub import Stubber

from wellspring._shared.errors.cloud_api_error import CloudApiError
from wellspring._shared.sdks.s3_sdk import S3Sdk


@pytest.fixture
def stubbed() -> Iterator[tuple[S3Sdk, Stubber]]:
    client = boto3.client("s3", region_name="us-east-1", aws_access_key_id="x", aws_secret_access_key="x")
    stub = Stubber(client)
    stub.activate()

    def factory() -> BaseClient:
        return client

    yield S3Sdk(factory), stub
    stub.assert_no_pending_responses()
    stub.deactivate()


def test_put_and_get_bytes_split_bucket_and_key(stubbed: tuple[S3Sdk, Stubber]) -> None:
    sdk, stub = stubbed
    stub.add_response("put_object", {}, {"Bucket": "bkt", "Key": "pre/run/request.json", "Body": b"{}"})
    asyncio.run(sdk.put_bytes("s3://bkt/pre/run/request.json", b"{}"))
    body = StreamingBody(BytesIO(b"hello"), 5)
    stub.add_response("get_object", {"Body": body}, {"Bucket": "bkt", "Key": "pre/run/status.json"})
    assert asyncio.run(sdk.get_bytes("s3://bkt/pre/run/status.json")) == b"hello"


def test_list_returns_full_uris(stubbed: tuple[S3Sdk, Stubber]) -> None:
    sdk, stub = stubbed
    stub.add_response("list_objects_v2", {"Contents": [{"Key": "pre/run/outputs/a"}, {"Key": "pre/run/outputs/b/c"}],
                                          "IsTruncated": False},
                      {"Bucket": "bkt", "Prefix": "pre/run/outputs/"})
    assert asyncio.run(sdk.list("s3://bkt/pre/run/outputs/")) == [
        "s3://bkt/pre/run/outputs/a", "s3://bkt/pre/run/outputs/b/c"]


def test_exists_is_false_on_404(stubbed: tuple[S3Sdk, Stubber]) -> None:
    sdk, stub = stubbed
    stub.add_client_error("head_object", service_error_code="404", http_status_code=404,
                          expected_params={"Bucket": "bkt", "Key": "pre/run/checksums.sha256"})
    assert asyncio.run(sdk.exists("s3://bkt/pre/run/checksums.sha256")) is False
    stub.add_response("head_object", {}, {"Bucket": "bkt", "Key": "pre/run/checksums.sha256"})
    assert asyncio.run(sdk.exists("s3://bkt/pre/run/checksums.sha256")) is True


def test_every_public_method_is_a_coroutine_and_there_is_no_delete() -> None:
    public = [n for n in dir(S3Sdk) if not n.startswith("_")]
    assert public and all(inspect.iscoroutinefunction(getattr(S3Sdk, n)) for n in public)
    assert not any("delete" in n or "remove" in n for n in public)


def test_access_denied_becomes_a_typed_cloud_error(stubbed: tuple[S3Sdk, Stubber]) -> None:
    sdk, stub = stubbed
    stub.add_client_error("get_object", service_error_code="AccessDenied", service_message="Access Denied",
                          http_status_code=403)
    with pytest.raises(CloudApiError) as exc:
        asyncio.run(sdk.get_bytes("s3://bkt/pre/run/request.json"))
    assert exc.value.code == "AccessDenied" and "s3://bkt/pre/run/request.json" in str(exc.value)
