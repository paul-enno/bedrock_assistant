"""The Bedrock Agent integration."""

from __future__ import annotations

import logging

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, SupportsResponse

from .agent import BedrockAgent
from .const import DOMAIN
from .services import COGNITIVE_TASK_SCHEMA, CognitiveTaskService

_LOGGER = logging.getLogger(__name__)
__all__ = [
    "async_setup_entry",
    "async_unload_entry",
    "async_migrate_entry",
    "options_update_listener",
]

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)
    if config_entry.version == 1:
        hass.config_entries.async_update_entry(
            config_entry, data=config_entry.data, minor_version=1, version=2
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bedrock Agent from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create and register the conversation agent
    bedrock_agent = BedrockAgent(hass, entry)
    conversation.async_set_agent(hass, entry, bedrock_agent)

    # Store entry data and setup listener
    hass_data = dict(entry.data)
    unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    hass_data["unsub_options_update_listener"] = unsub_options_update_listener
    hass_data["agent"] = bedrock_agent
    hass.data[DOMAIN][entry.entry_id] = hass_data

    # Register cognitive task service
    service_handler = CognitiveTaskService(hass, bedrock_agent)
    hass.services.async_register(
        DOMAIN,
        "cognitive_task",
        service_handler.async_handle_cognitive_task,
        schema=COGNITIVE_TASK_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    conversation.async_unset_agent(hass, entry)
    return True


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    # Reload could be implemented here if needed
    # await hass.config_entries.async_reload(config_entry.entry_id)

