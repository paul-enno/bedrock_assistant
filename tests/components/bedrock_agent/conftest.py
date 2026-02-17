"""Fixtures for Bedrock Agent tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.bedrock_agent.const import (
    CONST_KEY_ID,
    CONST_KEY_SECRET,
    CONST_MODEL_ID,
    CONST_PROMPT_CONTEXT,
    CONST_REGION,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


@pytest.fixture(autouse=True)
def mock_conversation_setup():
    """Mock conversation component setup to avoid dependency issues."""
    with patch(
        "homeassistant.components.conversation.async_set_agent"
    ) as mock_set_agent:
        yield mock_set_agent


@pytest.fixture
def mock_config_entry() -> ConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONST_KEY_ID: "test_key_id",
            CONST_KEY_SECRET: "test_key_secret",
            CONST_REGION: "us-east-1",
            "title": "Test Bedrock",
        },
        options={
            CONST_MODEL_ID: "anthropic.claude-v2",
            CONST_PROMPT_CONTEXT: "You are a helpful assistant. ",
        },
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_boto3_session() -> Generator[MagicMock]:
    """Mock boto3.Session."""
    with patch("homeassistant.components.bedrock_agent.aws_client.boto3.Session") as mock:
        session = MagicMock()
        mock.return_value = session
        yield mock


@pytest.fixture
def mock_boto3_client() -> Generator[AsyncMock]:
    """Mock boto3.client."""
    with patch("homeassistant.components.bedrock_agent.aws_client.boto3.client") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield mock


@pytest.fixture
def mock_bedrock_model() -> Generator[MagicMock]:
    """Mock BedrockModel."""
    with patch("homeassistant.components.bedrock_agent.strands_wrapper.BedrockModel") as mock:
        model = MagicMock()
        mock.return_value = model
        yield mock


@pytest.fixture
def mock_strands_agent() -> Generator[MagicMock]:
    """Mock strands Agent."""
    with patch("homeassistant.components.bedrock_agent.strands_wrapper.Agent") as mock:
        agent = MagicMock()
        agent.return_value = "Test response"
        mock.return_value = agent
        yield mock


@pytest.fixture
def mock_file_session_manager() -> Generator[MagicMock]:
    """Mock FileSessionManager."""
    with patch(
        "homeassistant.components.bedrock_agent.strands_wrapper.FileSessionManager"
    ) as mock:
        session_manager = MagicMock()
        mock.return_value = session_manager
        yield mock


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_boto3_client: AsyncMock,
    mock_strands_agent: MagicMock,
    mock_conversation_setup: MagicMock,
) -> ConfigEntry:
    """Set up the Bedrock Agent integration for testing."""
    mock_config_entry.add_to_hass(hass)
    
    # Mock llm.async_get_apis to return empty list
    with patch("homeassistant.components.bedrock_agent.agent.llm.async_get_apis", return_value=[]):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    
    return mock_config_entry
