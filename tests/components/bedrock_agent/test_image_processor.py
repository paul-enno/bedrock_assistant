"""Tests for image processor."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.error import HTTPError

import pytest

from homeassistant.components.bedrock_agent.image_processor import (
    ImageProcessor,
    build_converse_prompt_content,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError


@pytest.fixture
def image_processor(hass: HomeAssistant) -> ImageProcessor:
    """Create an image processor."""
    return ImageProcessor(hass)


@pytest.fixture
def mock_pil_image() -> MagicMock:
    """Create a mock PIL Image."""
    image = MagicMock()
    image.format = "jpeg"
    image.save = MagicMock()
    return image


async def test_build_converse_prompt_content(mock_pil_image: MagicMock) -> None:
    """Test converting PIL image to Bedrock format."""
    result = await build_converse_prompt_content(mock_pil_image)

    assert "image" in result
    assert "format" in result["image"]
    assert "source" in result["image"]
    assert result["image"]["format"] == "jpeg"


async def test_load_image_from_file_success(
    hass: HomeAssistant,
    image_processor: ImageProcessor,
    mock_pil_image: MagicMock,
) -> None:
    """Test successfully loading an image from file."""
    test_file = "/allowed/path/test.jpg"

    async def mock_executor_job(func, *args):
        # Call the function synchronously and return the result
        return mock_pil_image

    with (
        patch.object(hass.config, "is_allowed_path", return_value=True),
        patch.object(Path, "exists", return_value=True),
        patch("homeassistant.components.bedrock_agent.image_processor.mimetypes.guess_type", return_value=("image/jpeg", None)),
        patch("homeassistant.components.bedrock_agent.image_processor.PIL.Image.open", return_value=mock_pil_image),
        patch.object(hass, "async_add_executor_job", side_effect=mock_executor_job),
    ):
        result = await image_processor.load_image_from_file(test_file)

        assert result == mock_pil_image


async def test_load_image_from_file_not_allowed(
    hass: HomeAssistant,
    image_processor: ImageProcessor,
) -> None:
    """Test loading image from disallowed path."""
    test_file = "/not/allowed/test.jpg"

    with patch.object(hass.config, "is_allowed_path", return_value=False):
        with pytest.raises(HomeAssistantError, match="no access to path"):
            await image_processor.load_image_from_file(test_file)


async def test_load_image_from_file_not_exists(
    hass: HomeAssistant,
    image_processor: ImageProcessor,
) -> None:
    """Test loading non-existent image file."""
    test_file = "/allowed/path/missing.jpg"

    with (
        patch.object(hass.config, "is_allowed_path", return_value=True),
        patch.object(Path, "exists", return_value=False),
    ):
        with pytest.raises(HomeAssistantError, match="does not exist"):
            await image_processor.load_image_from_file(test_file)


async def test_load_image_from_file_not_image(
    hass: HomeAssistant,
    image_processor: ImageProcessor,
) -> None:
    """Test loading non-image file."""
    test_file = "/allowed/path/test.txt"

    with (
        patch.object(hass.config, "is_allowed_path", return_value=True),
        patch.object(Path, "exists", return_value=True),
        patch("homeassistant.components.bedrock_agent.image_processor.mimetypes.guess_type", return_value=("text/plain", None)),
    ):
        with pytest.raises(HomeAssistantError, match="is not an image"):
            await image_processor.load_image_from_file(test_file)


async def test_load_image_from_url_success(
    hass: HomeAssistant,
    image_processor: ImageProcessor,
    mock_pil_image: MagicMock,
) -> None:
    """Test successfully loading an image from URL."""
    test_url = "https://example.com/test.jpg"

    mock_url_response = MagicMock()
    
    async def mock_executor_job(func, *args):
        # Return mock URL response
        return mock_url_response

    with (
        patch("homeassistant.components.bedrock_agent.image_processor.mimetypes.guess_type", return_value=("image/jpeg", None)),
        patch("homeassistant.components.bedrock_agent.image_processor.PIL.Image.open", return_value=mock_pil_image),
        patch.object(hass, "async_add_executor_job", side_effect=mock_executor_job),
    ):
        result = await image_processor.load_image_from_url(test_url)

        assert result == mock_pil_image


async def test_load_image_from_url_http_error(
    hass: HomeAssistant,
    image_processor: ImageProcessor,
) -> None:
    """Test loading image from URL with HTTP error."""
    test_url = "https://example.com/test.jpg"

    http_error = HTTPError(test_url, 404, "Not Found", {}, None)

    with (
        patch("homeassistant.components.bedrock_agent.image_processor.mimetypes.guess_type", return_value=("image/jpeg", None)),
        patch.object(hass, "async_add_executor_job", side_effect=http_error),
    ):
        with pytest.raises(HomeAssistantError, match="Cannot access file"):
            await image_processor.load_image_from_url(test_url)
