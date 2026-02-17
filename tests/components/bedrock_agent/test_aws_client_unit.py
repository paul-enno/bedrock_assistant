"""Unit tests for AWS client factory."""

from unittest.mock import MagicMock, patch

import pytest

from homeassistant.components.bedrock_agent.aws_client import AWSClientFactory
from homeassistant.core import HomeAssistant


def test_aws_factory_initialization(hass: HomeAssistant) -> None:
    """Test AWS factory initialization."""
    factory = AWSClientFactory(
        hass=hass,
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        region_name="us-east-1",
    )

    assert factory.aws_access_key_id == "test_key"
    assert factory.aws_secret_access_key == "test_secret"
    assert factory.region_name == "us-east-1"


def test_create_boto3_session(hass: HomeAssistant) -> None:
    """Test creating a boto3 session."""
    factory = AWSClientFactory(
        hass=hass,
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        region_name="us-east-1",
    )

    with patch("homeassistant.components.bedrock_agent.aws_client.boto3.Session") as mock_session:
        session = factory.create_boto3_session()

        mock_session.assert_called_once_with(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            region_name="us-east-1",
        )
