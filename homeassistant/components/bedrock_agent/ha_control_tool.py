"""Home Assistant control tool for Strands Agent."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import threading
from typing import TYPE_CHECKING, Any

from strands.tools.decorator import tool

from homeassistant.helpers.llm import ToolInput as HAToolInput

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.llm import API, APIInstance, LLMContext, Tool

_LOGGER = logging.getLogger(__name__)


class HAToolRegistry:
    """Registry for Home Assistant tools."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self.api_instances: dict[str, APIInstance] = {}
        self.tools_by_name: dict[
            str, tuple[Tool, str]
        ] = {}  # tool_name -> (tool, api_id)

    async def async_load_apis(
        self,
        hass: HomeAssistant,
        apis: list[API],
        llm_context: LLMContext,
    ) -> None:
        """Load all API instances and their tools.

        Args:
            hass: Home Assistant instance
            apis: List of Home Assistant LLM APIs
            llm_context: LLM context
        """
        self.api_instances.clear()
        self.tools_by_name.clear()

        for api in apis:
            try:
                api_instance = await api.async_get_api_instance(llm_context)
                self.api_instances[api.id] = api_instance

                # Register all tools from this API
                for ha_tool in api_instance.tools:
                    self.tools_by_name[ha_tool.name] = (ha_tool, api.id)
                    _LOGGER.debug(
                        "Registered HA tool: %s from API: %s", ha_tool.name, api.id
                    )

                _LOGGER.debug(
                    "Loaded API: %s with %d tools", api.id, len(api_instance.tools)
                )

            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Failed to load API %s: %s", api.id, err)

        _LOGGER.info(
            "Loaded %d Home Assistant tools from %d APIs",
            len(self.tools_by_name),
            len(self.api_instances),
        )

    def get_tool_descriptions(self) -> str:
        """Get descriptions of all available tools.

        Returns:
            Formatted string with tool descriptions
        """
        if not self.tools_by_name:
            return "No Home Assistant tools available"

        descriptions = ["Available Home Assistant tools:"]
        for tool_name, (ha_tool, _api_id) in sorted(self.tools_by_name.items()):
            desc = ha_tool.description or "No description"
            descriptions.append(f"- {tool_name}: {desc}")

        return "\n".join(descriptions)

    async def async_call_tool(
        self,
        hass: HomeAssistant,
        tool_name: str,
        tool_args: dict[str, Any],
        llm_context: LLMContext,
    ) -> dict[str, Any]:
        """Call a Home Assistant tool by name.

        Args:
            hass: Home Assistant instance
            tool_name: Name of the tool to call
            tool_args: Arguments for the tool
            llm_context: LLM context

        Returns:
            Tool execution result
        """
        _LOGGER.debug(
            "Registry.async_call_tool: tool_name=%s, tool_args=%s",
            tool_name,
            tool_args,
        )

        if tool_name not in self.tools_by_name:
            available = ", ".join(sorted(self.tools_by_name.keys()))
            return {
                "error": f"Tool '{tool_name}' not found. Available tools: {available}"
            }

        ha_tool, api_id = self.tools_by_name[tool_name]

        try:
            _LOGGER.debug(
                "Calling HA tool %s from API %s with args: %s",
                tool_name,
                api_id,
                tool_args,
            )

            # Create tool input
            tool_input = HAToolInput(
                tool_name=tool_name,
                tool_args=tool_args,
            )

            # Call the HA tool - when agent runs in executor (memory enabled),
            # we're in a different event loop created by strands' asyncio.run().
            # We must ALWAYS schedule the HA tool call in the HA event loop.

            # Check if we're in the main thread (HA event loop thread)
            if threading.current_thread() == threading.main_thread():
                # We're in the HA event loop, call directly
                result = await ha_tool.async_call(hass, tool_input, llm_context)
            else:
                # We're in an executor thread, schedule in HA loop
                future = asyncio.run_coroutine_threadsafe(
                    ha_tool.async_call(hass, tool_input, llm_context),
                    hass.loop
                )
                result = await asyncio.wrap_future(future)

            _LOGGER.debug("HA tool %s raw result type: %s", tool_name, type(result).__name__)
            _LOGGER.debug("HA tool %s result: %s", tool_name, result)

            # Return result - format large responses more concisely
            if isinstance(result, dict):
                # Handle shopping list/todo responses that might be too large
                if result.get("success") and "result" in result:
                    result_data = result["result"]
                    _LOGGER.debug(
                        "Processing result for %s: type=%s, length=%s",
                        tool_name,
                        type(result_data).__name__,
                        len(result_data) if isinstance(result_data, list) else "N/A",
                    )
                    # If result is a list of items (shopping list), format concisely
                    if isinstance(result_data, list) and len(result_data) > 0:
                        # Check if it looks like todo items
                        first_item = result_data[0]
                        if isinstance(first_item, dict) and "summary" in first_item:
                            # Format as a simple string list to minimize size
                            items = [
                                item.get("summary", "")
                                for item in result_data
                                if isinstance(item, dict) and item.get("summary")
                            ]
                            # Return as a simple string to minimize JSON overhead
                            items_text = "\n".join(f"- {item}" for item in items)
                            formatted_result = {
                                "success": True,
                                "result": f"Shopping list has {len(items)} items:\n{items_text}"
                            }
                            _LOGGER.debug("Formatted todo response: %s", formatted_result)
                            return formatted_result

                        _LOGGER.debug(
                            "First item doesn't look like todo item: %s",
                            first_item
                        )
                return result
            return {"result": str(result)}

        except Exception as err:
            _LOGGER.exception("Error calling HA tool %s", tool_name)

            # Provide helpful error messages for common issues
            error_msg = str(err)
            if "Failed to call turn_on" in error_msg and "scene." in error_msg:
                # Extract scene name from error
                scene_match = re.search(r"scene\.(\w+)", error_msg)
                scene_name = scene_match.group(1) if scene_match else "unknown"

                # Check if there's a direct tool for this scene
                if scene_name in self.tools_by_name:
                    return {
                        "error": f"Cannot use HassTurnOn for scenes. Use tool_name='{scene_name}' directly instead."
                    }
                return {
                    "error": "Scenes cannot be activated with HassTurnOn. Try using the scene name as tool_name directly, or check available tools with GetLiveContext."
                }

            return {"error": error_msg}


async def create_ha_control_tool(
    hass: HomeAssistant,
    apis: list[API],
    llm_context: LLMContext,
) -> Any:
    """Create a single Strands tool that dispatches to Home Assistant tools.

    Args:
        hass: Home Assistant instance
        apis: List of Home Assistant LLM APIs
        llm_context: LLM context

    Returns:
        Strands-compatible tool function
    """
    # Create and load the registry
    registry = HAToolRegistry()
    await registry.async_load_apis(hass, apis, llm_context)

    # Build tool description
    available_tools = "\n".join(
        f"- {tool_name}: {tool.description or 'No description'}"
        for tool_name, (tool, _) in sorted(registry.tools_by_name.items())
    )

    @tool(
        name="homeassistant_control",
        description=f"""Control Home Assistant devices and query their state. ALWAYS use this tool to get current, real-time information.

This is a SINGLE UNIFIED TOOL that provides access to all Home Assistant capabilities.
You access different functions by setting the 'tool_name' parameter.

USAGE:
Call homeassistant_control with:
1. tool_name: The function to execute (see available functions below)
2. name: The device/list name (REQUIRED for most functions)
3. Additional parameters based on the function type

CRITICAL FOR SHOPPING LISTS AND TODO LISTS:
- To see what's currently on a list, call: homeassistant_control(tool_name='todo_get_items', name='Shopping List')
- NEVER rely on conversation history or memory for list contents
- ALWAYS call todo_get_items every single time the user asks about list contents
- Even if you just called it, call it again if asked again - lists can change

CRITICAL FOR CALENDAR QUERIES:
- To check calendar events, call: homeassistant_control(tool_name='calendar_get_events', calendar='Calendar Name', range='today' or 'week')
- Use range='today' for today's events, range='week' for the next 7 days
- ALWAYS call this tool when asked about appointments, meetings, or schedule
- NEVER guess or remember calendar events from conversation history

AVAILABLE FUNCTIONS (accessed via tool_name parameter):
{available_tools}

EXAMPLES:
- Turn on light: homeassistant_control(tool_name='HassTurnOn', name='kitchen light', domain='light')
- Get temperature: homeassistant_control(tool_name='HassGetState', name='bedroom temperature')
- Add to list: homeassistant_control(tool_name='HassListAddItem', name='Shopping List', item='milk')
- Get shopping list: homeassistant_control(tool_name='todo_get_items', name='Shopping List')
- Today's calendar: homeassistant_control(tool_name='calendar_get_events', calendar='My Calendar', range='today')
- Week's calendar: homeassistant_control(tool_name='calendar_get_events', calendar='Work Calendar', range='week')
- List all devices: homeassistant_control(tool_name='GetLiveContext')
- Get date/time: homeassistant_control(tool_name='GetDateTime')
- Run script: homeassistant_control(tool_name='script_name') (if scripts are exposed)

IMPORTANT: All Home Assistant control goes through THIS SINGLE TOOL. Do NOT answer from memory.""",
    )
    async def homeassistant_control(
        tool_name: str,
        name: str = "",
        domain: str = "",
        brightness: int | None = None,
        color: str = "",
        item: str = "",
        calendar: str = "",
        range: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute a Home Assistant tool.

        Args:
            tool_name: Name of the HA tool/intent (e.g., 'HassTurnOn', 'HassGetState', 'calendar_get_events')
            name: Device/list name to control (REQUIRED for most intents)
            domain: Device domain (e.g., 'light', 'switch', 'fan')
            brightness: Light brightness 0-100 (for HassLightSet)
            color: Color name or value (for HassLightSet)
            item: Item to add/remove (for HassListAddItem, HassListRemoveItem)
            calendar: Calendar name (for calendar_get_events)
            range: Time range 'today' or 'week' (for calendar_get_events)
            **kwargs: Additional parameters for specific intents
        """
        _LOGGER.debug(
            "Homeassistant_control called: tool_name=%s, name='%s', domain='%s', brightness=%s, color='%s', item='%s', kwargs=%s",
            tool_name,
            name,
            domain,
            brightness,
            color,
            item,
            kwargs,
        )

        # Validate that name is provided for intents that require it
        intents_requiring_name = {
            # Device control intents
            "HassTurnOn",
            "HassTurnOff",
            "HassToggle",
            "HassGetState",
            "HassLightSet",
            "HassSetPosition",
            "HassMediaUnpause",
            "HassMediaPause",
            "HassMediaNext",
            "HassMediaPrevious",
            "HassSetVolume",
            # Shopping list / todo intents
            "HassListAddItem",
            "HassListRemoveItem",
            "todo_get_items",
        }

        if tool_name in intents_requiring_name and not name:
            error_msg = f"Intent '{tool_name}' requires a 'name' parameter. "

            # Provide specific guidance based on intent type
            if tool_name.startswith("HassList"):
                error_msg += "For shopping list intents, provide the list name (e.g., name='Shopping List')."
            else:
                error_msg += "For device control, provide the device name (e.g., name='kitchen light')."

            _LOGGER.error(error_msg)
            return {"error": error_msg}

        # Build tool args - only include non-empty values
        tool_args: dict[str, Any] = {}

        # Map parameters based on tool type
        # todo_get_items expects 'todo_list' instead of 'name'
        if tool_name == "todo_get_items":
            if name:
                tool_args["todo_list"] = name
        # calendar_get_events uses 'calendar' and 'range' parameters
        elif tool_name == "calendar_get_events":
            if calendar:
                tool_args["calendar"] = calendar
            if range:
                tool_args["range"] = range
        elif name:
            tool_args["name"] = name

        if domain:
            tool_args["domain"] = domain
        if brightness is not None:
            tool_args["brightness"] = brightness
        if color:
            tool_args["color"] = color
        if item:
            tool_args["item"] = item

        # Add any additional kwargs, but filter out:
        # - Empty/None values
        # - The 'kwargs' key itself (LLM sometimes sends this)
        tool_args.update({
            key: value
            for key, value in kwargs.items()
            if key != "kwargs" and value is not None and value not in {"", "{}"}
        })

        _LOGGER.debug("Calling HA tool %s with args: %s", tool_name, tool_args)

        result = await registry.async_call_tool(
            hass,
            tool_name,
            tool_args,
            llm_context,
        )

        # Ensure result is not too large for Strands SDK
        # Convert to string and check size
        result_str = json.dumps(result)
        result_size = len(result_str)
        _LOGGER.debug("Tool %s result size: %d bytes", tool_name, result_size)

        # If result is too large (>4KB), try to summarize it
        if result_size > 4096:
            _LOGGER.warning("Tool %s result too large (%d bytes), summarizing", tool_name, result_size)
            if isinstance(result, dict) and result.get("success") and "result" in result:
                result_data = result["result"]
                if isinstance(result_data, list):
                    # Summarize list results
                    return {
                        "success": True,
                        "result": f"Found {len(result_data)} items. Use a more specific query to see details."
                    }
                if isinstance(result_data, str) and len(result_data) > 1000:
                    # Truncate long strings
                    return {
                        "success": True,
                        "result": result_data[:1000] + f"... (truncated, {len(result_data)} total chars)"
                    }

        return result

    return homeassistant_control


# Tool specification for documentation
TOOL_SPEC = {
    "name": "homeassistant_control",
    "description": (
        "Control Home Assistant devices and query their state. "
        "This tool provides access to all Home Assistant intents and actions."
    ),
}
