import os

import boto3
import pytest
from moto import mock_ec2

pytest.aws_region = "us-east-1"


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "fake_id"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "fake_key"
    os.environ["AWS_SECURITY_TOKEN"] = "fake_security_token"
    os.environ["AWS_SESSION_TOKEN"] = "fake_session_token"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture()
def ec2(aws_credentials):
    with mock_ec2():
        conn = boto3.client("ec2")
        yield conn
