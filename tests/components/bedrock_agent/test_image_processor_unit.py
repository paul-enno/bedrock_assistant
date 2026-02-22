"""Unit tests for image processor."""

from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from homeassistant.components.bedrock_agent.image_processor import (
    ImageProcessor,
    build_converse_prompt_content,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError


async def test_build_converse_prompt_content() -> None:
    """Test converting PIL image to Bedrock format."""
    mock_image = MagicMock()
    mock_image.format = "jpeg"
    mock_image.save = MagicMock()

    result = await build_converse_prompt_content(mock_image)

    assert "image" in result
    assert "format" in result["image"]
    assert "source" in result["image"]
    assert result["image"]["format"] == "jpeg"
    mock_image.save.assert_called_once()


async def test_load_image_from_file_not_allowed(hass: HomeAssistant) -> None:
    """Test loading image from disallowed path."""
    processor = ImageProcessor(hass)
    test_file = "/not/allowed/test.jpg"

    with patch.object(hass.config, "is_allowed_path", return_value=False):
        with pytest.raises(HomeAssistantError, match="no access to path"):
            await processor.load_image_from_file(test_file)


async def test_load_image_from_file_not_exists(hass: HomeAssistant) -> None:
    """Test loading non-existent image file."""
    processor = ImageProcessor(hass)
    test_file = "/allowed/path/missing.jpg"

    with (
        patch.object(hass.config, "is_allowed_path", return_value=True),
        patch.object(Path, "exists", return_value=False),
    ):
        with pytest.raises(HomeAssistantError, match="does not exist"):
            await processor.load_image_from_file(test_file)


async def test_load_image_from_file_not_image(hass: HomeAssistant) -> None:
    """Test loading non-image file."""
    processor = ImageProcessor(hass)
    test_file = "/allowed/path/test.txt"

    with (
        patch.object(hass.config, "is_allowed_path", return_value=True),
        patch.object(Path, "exists", return_value=True),
        patch("homeassistant.components.bedrock_agent.image_processor.mimetypes.guess_type", return_value=("text/plain", None)),
    ):
        with pytest.raises(HomeAssistantError, match="is not an image"):
            await processor.load_image_from_file(test_file)


async def test_load_image_from_url_not_image(hass: HomeAssistant) -> None:
    """Test loading non-image from URL."""
    processor = ImageProcessor(hass)
    test_url = "https://example.com/test.txt"

    with patch("homeassistant.components.bedrock_agent.image_processor.mimetypes.guess_type", return_value=("text/plain", None)):
        with pytest.raises(HomeAssistantError, match="is not an image"):
            await processor.load_image_from_url(test_url)
