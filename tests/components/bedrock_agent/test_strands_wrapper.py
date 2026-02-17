"""Tests for Strands wrapper."""

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
import pytest

from homeassistant.components.bedrock_agent.aws_client import AWSClientFactory
from homeassistant.components.bedrock_agent.strands_wrapper import StrandsAgentWrapper
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError


@pytest.fixture
def aws_factory(hass: HomeAssistant) -> AWSClientFactory:
    """Create an AWS client factory."""
    return AWSClientFactory(
        hass=hass,
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        region_name="us-east-1",
    )


@pytest.fixture
def strands_wrapper(
    hass: HomeAssistant,
    aws_factory: AWSClientFactory,
    mock_strands_agent: MagicMock,
    mock_bedrock_model: MagicMock,
    mock_file_session_manager: MagicMock,
) -> StrandsAgentWrapper:
    """Create a strands wrapper."""
    return StrandsAgentWrapper(
        hass=hass,
        aws_factory=aws_factory,
        model_id="anthropic.claude-v2",
        apis=[],
        system_prompt="Test prompt",
        session_id="test-session",
    )


async def test_generate_response_success(
    hass: HomeAssistant,
    strands_wrapper: StrandsAgentWrapper,
) -> None:
    """Test successful response generation."""
    with patch.object(
        hass, "async_add_executor_job", return_value="Test response"
    ):
        result = await strands_wrapper.generate_response("Test prompt")

        assert result == "Test response"


async def test_generate_response_client_error(
    hass: HomeAssistant,
    strands_wrapper: StrandsAgentWrapper,
) -> None:
    """Test response generation with client error."""
    error_response = {"Error": {"Message": "Test error"}}
    client_error = ClientError(error_response, "test_operation")

    with patch.object(
        hass, "async_add_executor_job", side_effect=client_error
    ):
        with pytest.raises(HomeAssistantError, match="Amazon Bedrock Error"):
            await strands_wrapper.generate_response("Test prompt")


def test_get_agent_with_session_and_prompt(
    strands_wrapper: StrandsAgentWrapper,
    mock_strands_agent: MagicMock,
    mock_bedrock_model: MagicMock,
    mock_file_session_manager: MagicMock,
) -> None:
    """Test getting agent with session and system prompt."""
    agent = strands_wrapper.get_agent("test-model", True, True)

    assert agent is not None
    mock_strands_agent.assert_called()


def test_get_agent_without_session(
    strands_wrapper: StrandsAgentWrapper,
    mock_strands_agent: MagicMock,
    mock_bedrock_model: MagicMock,
) -> None:
    """Test getting agent without session."""
    agent = strands_wrapper.get_agent("test-model", False, True)

    assert agent is not None


def test_get_agent_without_prompt(
    strands_wrapper: StrandsAgentWrapper,
    mock_strands_agent: MagicMock,
    mock_bedrock_model: MagicMock,
    mock_file_session_manager: MagicMock,
) -> None:
    """Test getting agent without system prompt."""
    agent = strands_wrapper.get_agent("test-model", True, False)

    assert agent is not None


async def test_async_call_llm(
    hass: HomeAssistant,
    strands_wrapper: StrandsAgentWrapper,
) -> None:
    """Test calling LLM through wrapper."""
    with patch.object(
        hass, "async_add_executor_job", return_value="LLM response"
    ):
        result = await strands_wrapper.async_call_llm("Test prompt", None)

        assert result == "LLM response"
