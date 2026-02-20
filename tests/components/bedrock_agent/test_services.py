"""Tests for Bedrock services."""

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
import pytest

from homeassistant.components.bedrock_agent.services import CognitiveTaskService
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError


@pytest.fixture
def mock_service_call(hass: HomeAssistant) -> ServiceCall:
    """Create a mock service call."""
    return ServiceCall(
        hass=hass,
        domain="bedrock_agent",
        service="cognitive_task",
        data={
            "prompt": "Describe this image",
            "model_id": "anthropic.claude-v2",
            "image_filenames": [],
            "image_urls": [],
        },
    )


async def test_cognitive_task_text_only(
    hass: HomeAssistant,
    init_integration: ConfigEntry,
    mock_service_call: ServiceCall,
) -> None:
    """Test cognitive task with text only."""
    agent_instance = hass.data["bedrock_agent"][init_integration.entry_id]["agent"]
    service = CognitiveTaskService(hass, agent_instance)

    mock_agent = MagicMock()
    mock_agent.return_value = "Image description"

    with patch.object(
        agent_instance.strands_agent_wrapper,
        "get_simple_agent",
        return_value=mock_agent,
    ):
        result = await service.async_handle_cognitive_task(mock_service_call)

        assert result["text"] == "Image description"


async def test_cognitive_task_with_image_file(
    hass: HomeAssistant,
    init_integration: ConfigEntry,
) -> None:
    """Test cognitive task with image file."""
    agent_instance = hass.data["bedrock_agent"][init_integration.entry_id]["agent"]
    service = CognitiveTaskService(hass, agent_instance)

    service_call = ServiceCall(
        hass=hass,
        domain="bedrock_agent",
        service="cognitive_task",
        data={
            "prompt": "Describe this image",
            "image_filenames": ["/allowed/test.jpg"],
        },
    )

    mock_image = MagicMock()
    mock_image.format = "jpeg"
    
    mock_agent = MagicMock()
    mock_agent.return_value = "Image with file"

    with (
        patch.object(
            agent_instance.strands_agent_wrapper,
            "get_simple_agent",
            return_value=mock_agent,
        ),
        patch.object(
            service.image_processor,
            "load_image_from_file",
            return_value=mock_image,
        ),
    ):
        result = await service.async_handle_cognitive_task(service_call)

        assert result["text"] == "Image with file"


async def test_cognitive_task_with_image_url(
    hass: HomeAssistant,
    init_integration: ConfigEntry,
) -> None:
    """Test cognitive task with image URL."""
    agent_instance = hass.data["bedrock_agent"][init_integration.entry_id]["agent"]
    service = CognitiveTaskService(hass, agent_instance)

    service_call = ServiceCall(
        hass=hass,
        domain="bedrock_agent",
        service="cognitive_task",
        data={
            "prompt": "Describe this image",
            "image_urls": ["https://example.com/test.jpg"],
        },
    )

    mock_image = MagicMock()
    mock_image.format = "jpeg"
    
    mock_agent = MagicMock()
    mock_agent.return_value = "Image from URL"

    with (
        patch.object(
            agent_instance.strands_agent_wrapper,
            "get_simple_agent",
            return_value=mock_agent,
        ),
        patch.object(
            service.image_processor,
            "load_image_from_url",
            return_value=mock_image,
        ),
    ):
        result = await service.async_handle_cognitive_task(service_call)

        assert result["text"] == "Image from URL"


async def test_cognitive_task_client_error(
    hass: HomeAssistant,
    init_integration: ConfigEntry,
    mock_service_call: ServiceCall,
) -> None:
    """Test cognitive task with Bedrock client error."""
    agent_instance = hass.data["bedrock_agent"][init_integration.entry_id]["agent"]
    service = CognitiveTaskService(hass, agent_instance)

    error_response = {"Error": {"Message": "Rate limit exceeded"}}
    client_error = ClientError(error_response, "invoke_model")

    mock_agent = MagicMock()
    mock_agent.side_effect = client_error

    with patch.object(
        agent_instance.strands_agent_wrapper,
        "get_simple_agent",
        return_value=mock_agent,
    ):
        with pytest.raises(HomeAssistantError, match="Bedrock Error"):
            await service.async_handle_cognitive_task(mock_service_call)
