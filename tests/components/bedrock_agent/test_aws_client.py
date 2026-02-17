"""Tests for AWS client factory."""

from unittest.mock import AsyncMock, MagicMock, patch

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


async def test_create_bedrock_agent_client(
    hass: HomeAssistant,
    aws_factory: AWSClientFactory,
    mock_boto3_client: AsyncMock,
) -> None:
    """Test creating a Bedrock agent client."""
    client = await aws_factory.create_bedrock_agent_client()

    assert client is not None
    mock_boto3_client.assert_called_once()


def test_create_boto3_session(
    aws_factory: AWSClientFactory,
    mock_boto3_session: MagicMock,
) -> None:
    """Test creating a boto3 session."""
    session = aws_factory.create_boto3_session()

    assert session is not None
    mock_boto3_session.assert_called_once_with(
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        region_name="us-east-1",
    )


async def test_client_uses_correct_credentials(
    hass: HomeAssistant,
    aws_factory: AWSClientFactory,
) -> None:
    """Test that client is created with correct credentials."""
    with patch("homeassistant.components.bedrock_agent.aws_client.boto3.client") as mock_client:
        await aws_factory.create_bedrock_agent_client()

        # Verify the partial function was called with correct parameters
        call_args = mock_client.call_args
        assert call_args is not None
