"""Fixtures for Bedrock Agent tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.bedrock_agent.const import (
    CONST_ENABLE_HA_CONTROL,
    CONST_ENABLE_MEMORY,
    CONST_KEY_ID,
    CONST_KEY_SECRET,
    CONST_MEMORY_GUIDELINES,
    CONST_MEMORY_STORAGE_PATH,
    CONST_MODEL_ID,
    CONST_PROMPT_CONTEXT,
    CONST_REGION,
    DEFAULT_MEMORY_GUIDELINES,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry


@pytest.fixture(autouse=True)
async def setup_ha(hass: HomeAssistant) -> None:
    """Set up Home Assistant."""
    assert await async_setup_component(hass, "homeassistant", {})


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
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
            CONST_PROMPT_CONTEXT: "You are a helpful assistant.",
            CONST_ENABLE_HA_CONTROL: True,
            CONST_ENABLE_MEMORY: False,
            CONST_MEMORY_STORAGE_PATH: "",
            CONST_MEMORY_GUIDELINES: DEFAULT_MEMORY_GUIDELINES,
        },
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_config_entry_with_memory() -> MockConfigEntry:
    """Return a mock config entry with memory enabled."""
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
            CONST_PROMPT_CONTEXT: "You are a helpful assistant.",
            CONST_ENABLE_HA_CONTROL: True,
            CONST_ENABLE_MEMORY: True,  # Memory enabled
            CONST_MEMORY_STORAGE_PATH: "",
            CONST_MEMORY_GUIDELINES: DEFAULT_MEMORY_GUIDELINES,
        },
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_boto3_session() -> Generator[MagicMock]:
    """Mock boto3.Session."""
    with patch("boto3.Session") as mock:
        session = MagicMock()
        # Mock the client method to return a mock bedrock-runtime client
        bedrock_client = MagicMock()
        bedrock_client.converse.return_value = {
            "output": {"message": {"content": [{"text": "Test response"}]}},
            "stopReason": "end_turn",
        }
        session.client.return_value = bedrock_client
        mock.return_value = session
        yield mock


@pytest.fixture
def mock_boto3_client() -> Generator[MagicMock]:
    """Mock boto3.client for config flow validation."""
    with patch("boto3.client") as mock:
        client = MagicMock()
        # Mock list_foundation_models for config flow
        client.list_foundation_models.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200},
            "modelSummaries": [
                {
                    "modelId": "anthropic.claude-v2",
                    "modelName": "Claude v2",
                    "providerName": "Anthropic",
                }
            ],
        }
        # Mock list_inference_profiles for config flow
        client.list_inference_profiles.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200},
            "inferenceProfileSummaries": [],
        }
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
        
        # Mock invoke_async to return a response
        async def mock_invoke_async(prompt):
            response = MagicMock()
            response.message = {
                "content": [{"text": "Test response from agent"}]
            }
            return response
        
        agent.invoke_async = mock_invoke_async
        
        # Mock synchronous call for executor
        def mock_call(prompt):
            response = MagicMock()
            response.message = {
                "content": [{"text": "Test response from agent"}]
            }
            return response
        
        agent.__call__ = mock_call
        
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
def mock_sliding_window_manager() -> Generator[MagicMock]:
    """Mock SlidingWindowConversationManager."""
    with patch(
        "homeassistant.components.bedrock_agent.strands_wrapper.SlidingWindowConversationManager"
    ) as mock:
        manager = MagicMock()
        mock.return_value = manager
        yield mock


@pytest.fixture
def mock_mem0_memory() -> Generator[MagicMock]:
    """Mock mem0_memory tool."""
    with patch(
        "homeassistant.components.bedrock_agent.strands_wrapper.mem0_memory"
    ) as mock:
        tool = MagicMock()
        mock.return_value = tool
        yield mock


@pytest.fixture
def mock_llm_apis() -> Generator[MagicMock]:
    """Mock llm.async_get_apis."""
    with patch(
        "homeassistant.components.bedrock_agent.agent.llm.async_get_apis"
    ) as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_conversation_setup() -> Generator[MagicMock]:
    """Mock conversation component setup."""
    with patch(
        "homeassistant.components.conversation.async_set_agent"
    ) as mock_set_agent:
        yield mock_set_agent


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_boto3_session: MagicMock,
    mock_bedrock_model: MagicMock,
    mock_strands_agent: MagicMock,
    mock_file_session_manager: MagicMock,
    mock_sliding_window_manager: MagicMock,
    mock_llm_apis: MagicMock,
    mock_conversation_setup: MagicMock,
) -> MockConfigEntry:
    """Set up the Bedrock Agent integration for testing."""
    mock_config_entry.add_to_hass(hass)
    
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    
    return mock_config_entry

