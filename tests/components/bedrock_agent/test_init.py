"""Tests for Bedrock Agent integration setup."""

from unittest.mock import patch

from homeassistant.components.bedrock_agent.const import DOMAIN
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant


async def test_setup_entry(
    hass: HomeAssistant,
    init_integration: ConfigEntry,
) -> None:
    """Test successful setup of config entry."""
    assert init_integration.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert init_integration.entry_id in hass.data[DOMAIN]


async def test_unload_entry(
    hass: HomeAssistant,
    init_integration: ConfigEntry,
) -> None:
    """Test successful unload of config entry."""
    with patch("homeassistant.components.conversation.async_unset_agent"):
        assert await hass.config_entries.async_unload(init_integration.entry_id)
        await hass.async_block_till_done()

    assert init_integration.state == ConfigEntryState.NOT_LOADED


async def test_setup_entry_stores_agent(
    hass: HomeAssistant,
    init_integration: ConfigEntry,
) -> None:
    """Test that setup stores the agent instance."""
    entry_data = hass.data[DOMAIN][init_integration.entry_id]
    assert "agent" in entry_data
    assert entry_data["agent"] is not None


async def test_setup_registers_service(
    hass: HomeAssistant,
    init_integration: ConfigEntry,
) -> None:
    """Test that setup registers the cognitive_task service."""
    assert hass.services.has_service(DOMAIN, "cognitive_task")
