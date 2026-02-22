"""Tests for Strands wrapper."""

from unittest.mock import MagicMock, patch

import pytest

from homeassistant.components.bedrock_agent.aws_client import AWSClientFactory
from homeassistant.components.bedrock_agent.strands_wrapper import StrandsAgentWrapper
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


async def test_wrapper_initialization(
    hass: HomeAssistant,
    aws_factory: AWSClientFactory,
) -> None:
    """Test wrapper initialization."""
    with (
        patch("homeassistant.components.bedrock_agent.strands_wrapper.BedrockModel", return_value=MagicMock()),
        patch("homeassistant.components.bedrock_agent.strands_wrapper.Agent", return_value=MagicMock()),
        patch("homeassistant.components.bedrock_agent.strands_wrapper.FileSessionManager", return_value=MagicMock()),
        patch("homeassistant.components.bedrock_agent.strands_wrapper.SlidingWindowConversationManager", return_value=MagicMock()),
    ):
        wrapper = StrandsAgentWrapper(
            hass=hass,
            aws_factory=aws_factory,
            model_id="anthropic.claude-v2",
            apis=[],
            system_prompt="Test prompt",
            enable_memory=False,
        )
        
        assert wrapper.hass == hass
        assert wrapper.aws_factory == aws_factory
        assert wrapper.model_id == "anthropic.claude-v2"
        assert wrapper.system_prompt == "Test prompt"
        assert wrapper.enable_memory is False


async def test_get_agent_with_memory(
    hass: HomeAssistant,
    aws_factory: AWSClientFactory,
) -> None:
    """Test getting agent with memory enabled."""
    with (
        patch("homeassistant.components.bedrock_agent.strands_wrapper._mem0_available", True),
        patch("homeassistant.components.bedrock_agent.strands_wrapper.mem0_memory", MagicMock()),
        patch("homeassistant.components.bedrock_agent.strands_wrapper.BedrockModel", return_value=MagicMock()),
        patch("homeassistant.components.bedrock_agent.strands_wrapper.Agent", return_value=MagicMock()),
        patch("homeassistant.components.bedrock_agent.strands_wrapper.FileSessionManager", return_value=MagicMock()),
        patch("homeassistant.components.bedrock_agent.strands_wrapper.SlidingWindowConversationManager", return_value=MagicMock()),
    ):
        wrapper = StrandsAgentWrapper(
            hass=hass,
            aws_factory=aws_factory,
            model_id="anthropic.claude-v2",
            apis=[],
            system_prompt="Test prompt",
            enable_memory=True,
            memory_storage_path="/tmp/test",
        )
        
        # Memory should be enabled
        assert wrapper.enable_memory is True


async def test_get_simple_agent(
    hass: HomeAssistant,
    aws_factory: AWSClientFactory,
) -> None:
    """Test getting simple agent without session."""
    wrapper = StrandsAgentWrapper(
        hass=hass,
        aws_factory=aws_factory,
        model_id="anthropic.claude-v2",
        apis=[],
        system_prompt="Test prompt",
        enable_memory=False,
    )
    
    mock_agent = MagicMock()
    
    async def mock_executor_job(func, *args):
        return mock_agent
    
    with (
        patch("homeassistant.components.bedrock_agent.strands_wrapper.BedrockModel", return_value=MagicMock()),
        patch("homeassistant.components.bedrock_agent.strands_wrapper.Agent", return_value=mock_agent),
        patch.object(hass, "async_add_executor_job", side_effect=mock_executor_job),
    ):
        agent = await wrapper.get_simple_agent("test-model")
        assert agent is not None


async def test_clear_cache(
    hass: HomeAssistant,
    aws_factory: AWSClientFactory,
) -> None:
    """Test clearing agent cache."""
    with (
        patch("homeassistant.components.bedrock_agent.strands_wrapper.BedrockModel", return_value=MagicMock()),
        patch("homeassistant.components.bedrock_agent.strands_wrapper.Agent", return_value=MagicMock()),
        patch("homeassistant.components.bedrock_agent.strands_wrapper.FileSessionManager", return_value=MagicMock()),
        patch("homeassistant.components.bedrock_agent.strands_wrapper.SlidingWindowConversationManager", return_value=MagicMock()),
    ):
        wrapper = StrandsAgentWrapper(
            hass=hass,
            aws_factory=aws_factory,
            model_id="anthropic.claude-v2",
            apis=[],
            system_prompt="Test prompt",
            enable_memory=False,
        )
        
        # Add some agents to cache
        wrapper._agent_cache["user1"] = MagicMock()
        wrapper._agent_cache["user2"] = MagicMock()
        
        # Clear specific user
        wrapper.clear_user_cache("user1")
        assert "user1" not in wrapper._agent_cache
        assert "user2" in wrapper._agent_cache
        
        # Clear all
        wrapper.clear_all_cache()
        assert len(wrapper._agent_cache) == 0
