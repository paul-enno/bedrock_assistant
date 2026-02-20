"""Tests for AWS client factory."""

from unittest.mock import patch

import pytest

from homeassistant.components.bedrock_agent.aws_client import AWSClientFactory
from homeassistant.core import HomeAssistant


@pytest.fixture
def aws_factory(hass: HomeAssistant) -> AWSClientFactory:
    """Create an AWS client factory."""
    return AWSClientFactory(
        hass=hass,
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        region_name="us-east-1",
    )


def test_aws_factory_initialization(
    hass: HomeAssistant,
    aws_factory: AWSClientFactory,
) -> None:
    """Test AWS factory initialization."""
    assert aws_factory.hass == hass
    assert aws_factory.aws_access_key_id == "test_key"
    assert aws_factory.aws_secret_access_key == "test_secret"
    assert aws_factory.region_name == "us-east-1"


def test_create_boto3_session(
    aws_factory: AWSClientFactory,
) -> None:
    """Test creating a boto3 session."""
    with patch("homeassistant.components.bedrock_agent.aws_client.boto3.Session") as mock_session:
        session = aws_factory.create_boto3_session()

        assert session is not None
        mock_session.assert_called_once_with(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            region_name="us-east-1",
        )
