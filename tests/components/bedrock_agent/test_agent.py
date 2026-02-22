"""Tests for Bedrock conversation agent."""

from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

from homeassistant.components.bedrock_agent.agent import BedrockAgent
from homeassistant.components.conversation import agent_manager
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.intent import IntentResponseErrorCode


@pytest.fixture
def mock_conversation_input(hass: HomeAssistant) -> agent_manager.ConversationInput:
    """Create a mock conversation input."""
    context = MagicMock()
    context.user_id = "test_user_id"
    
    return agent_manager.ConversationInput(
        text="Test question",
        context=context,
        language="en",
        conversation_id=uuid.uuid4().hex,
        device_id="test_device",
        satellite_id=None,
        agent_id=None,
    )


async def test_agent_initialization(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_boto3_client: AsyncMock,
    mock_strands_agent: MagicMock,
) -> None:
    """Test agent initialization."""
    agent = BedrockAgent(hass, mock_config_entry)

    assert agent.hass == hass
    assert agent.entry == mock_config_entry
    assert agent.history == {}


async def test_supported_languages(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_boto3_client: AsyncMock,
    mock_strands_agent: MagicMock,
) -> None:
    """Test supported languages returns MATCH_ALL."""
    agent = BedrockAgent(hass, mock_config_entry)

    assert agent.supported_languages == "*"


async def test_supported_models(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_boto3_client: AsyncMock,
    mock_strands_agent: MagicMock,
) -> None:
    """Test supported models returns list."""
    agent = BedrockAgent(hass, mock_config_entry)

    models = agent.supported_models()
    assert isinstance(models, list)
    assert len(models) > 0


async def test_async_process_success(
    hass: HomeAssistant,
    init_integration: ConfigEntry,
    mock_conversation_input: agent_manager.ConversationInput,
) -> None:
    """Test successful conversation processing."""
    agent_instance = hass.data["bedrock_agent"][init_integration.entry_id]["agent"]

    with patch.object(
        agent_instance.strands_agent_wrapper,
        "generate_response",
        return_value="Test answer",
    ):
        result = await agent_instance.async_process(mock_conversation_input)

        assert result.response.speech["plain"]["speech"] == "Test answer"
        assert result.conversation_id == mock_conversation_input.conversation_id


async def test_async_process_generates_conversation_id(
    hass: HomeAssistant,
    init_integration: ConfigEntry,
) -> None:
    """Test conversation ID generation when not provided."""
    agent_instance = hass.data["bedrock_agent"][init_integration.entry_id]["agent"]

    context = MagicMock()
    context.user_id = "test_user_id"
    
    conversation_input = agent_manager.ConversationInput(
        text="Test question",
        context=context,
        language="en",
        conversation_id=None,
        device_id="test_device",
        satellite_id=None,
        agent_id=None,
    )

    with patch.object(
        agent_instance.strands_agent_wrapper,
        "generate_response",
        return_value="Test answer",
    ):
        result = await agent_instance.async_process(conversation_input)

        assert result.conversation_id is not None
        assert len(result.conversation_id) > 0


async def test_async_process_error_handling(
    hass: HomeAssistant,
    init_integration: ConfigEntry,
    mock_conversation_input: agent_manager.ConversationInput,
) -> None:
    """Test error handling in conversation processing."""
    agent_instance = hass.data["bedrock_agent"][init_integration.entry_id]["agent"]

    with patch.object(
        agent_instance.strands_agent_wrapper,
        "generate_response",
        side_effect=HomeAssistantError("Test error"),
    ):
        result = await agent_instance.async_process(mock_conversation_input)

        assert result.response.error_code == IntentResponseErrorCode.FAILED_TO_HANDLE
