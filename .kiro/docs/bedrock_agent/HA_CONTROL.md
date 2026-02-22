# Home Assistant Control Integration

This document describes how the Bedrock Agent integration provides Home Assistant device control capabilities through the Strands agent.

## Overview

The integration creates a single `homeassistant_control` tool that acts as a dispatcher to all Home Assistant intents and actions. This allows the LLM to control smart home devices, query their state, and interact with Home Assistant functionality.

## Architecture

### Components

1. **HAToolRegistry**: Manages the registry of available Home Assistant tools
   - Loads all API instances and their tools
   - Maintains a mapping of tool names to tool instances
   - Provides tool descriptions for the LLM
   - Dispatches tool calls to the appropriate Home Assistant tool

2. **create_ha_control_tool()**: Creates the Strands-compatible dispatcher tool
   - Loads all Home Assistant APIs and their tools
   - Creates a single tool decorated with `@tool` from Strands
   - Returns an async function that dispatches to HA tools

3. **StrandsAgentWrapper Integration**: Adds the HA control tool to agents
   - Calls `create_ha_control_tool()` when creating agents
   - Passes the tool to the Strands Agent
   - Enhances system prompt with usage instructions

## How It Works

### Tool Loading Process

1. When an agent is created, `create_ha_control_tool()` is called
2. It creates a `HAToolRegistry` instance
3. The registry loads all Home Assistant LLM APIs (e.g., AssistAPI)
4. For each API, it gets the API instance with the LLM context
5. Each API instance provides a list of tools (intents like HassTurnOn, HassGetState, etc.)
6. All tools are registered in the registry with their names and descriptions
7. A single Strands tool is created that dispatches to these HA tools

### Tool Execution Flow

1. LLM decides to use the `homeassistant_control` tool
2. LLM provides `tool_name` (e.g., "HassTurnOn") and parameters (e.g., name="kitchen light")
3. Strands calls the `homeassistant_control` function
4. The function calls `registry.async_call_tool()` with the tool name and args
5. Registry looks up the tool by name
6. Registry creates a `ToolInput` object with the parameters
7. Registry calls the Home Assistant tool's `async_call()` method
8. The HA tool executes the intent (e.g., turns on the light)
9. Result is returned to the LLM

## Available Tools

The exact tools available depend on the Home Assistant configuration and exposed entities. Common tools include:

### Device Control
- **HassTurnOn**: Turn devices on (lights, switches, fans, etc.)
  - Required: `name` (device name)
  - Optional: `domain` (e.g., "light", "switch")
  
- **HassTurnOff**: Turn devices off
  - Required: `name` (device name)
  - Optional: `domain`

- **HassLightSet**: Control light settings
  - Required: `name` (light name)
  - Optional: `brightness`, `color`, `color_temp`, etc.

### State Queries
- **HassGetState**: Get the current state of a device
  - Required: `name` (device name)
  
- **GetLiveContext**: Get current state of all exposed entities
  - No parameters required

### Date/Time
- **GetDateTime**: Get current date and time
  - No parameters required

### Other Intents
- **HassSetPosition**: Set position for covers, blinds, etc.
- **HassMediaUnpause**, **HassMediaPause**: Media control
- **HassSetVolume**: Volume control
- And many more depending on configuration

## Usage Examples

### Example 1: Turn on a light

**User**: "Turn on the kitchen light"

**LLM Tool Call**:
```python
homeassistant_control(
    tool_name="HassTurnOn",
    name="kitchen light",
    domain="light"
)
```

**Result**: Kitchen light is turned on

### Example 2: Check device state

**User**: "Is the living room light on?"

**LLM Tool Call**:
```python
homeassistant_control(
    tool_name="HassGetState",
    name="living room light"
)
```

**Result**: Returns state information (on/off, brightness, etc.)

### Example 3: Get all device states

**User**: "What devices are currently on?"

**LLM Tool Call**:
```python
homeassistant_control(
    tool_name="GetLiveContext"
)
```

**Result**: Returns YAML dump of all exposed entities and their states

### Example 4: Set light brightness

**User**: "Set bedroom light to 50% brightness"

**LLM Tool Call**:
```python
homeassistant_control(
    tool_name="HassLightSet",
    name="bedroom light",
    brightness=50
)
```

**Result**: Bedroom light brightness set to 50%

## Configuration

### Enabling HA Control

HA control is automatically enabled when:
1. The integration has access to Home Assistant LLM APIs
2. An LLM context is provided (contains user context, assistant info, etc.)

No additional configuration is required.

### System Prompt Enhancement

When HA control is enabled, the system prompt is automatically enhanced with:
- Instructions on how to use the `homeassistant_control` tool
- List of common tools and their parameters
- Examples of proper usage
- Warnings about parameter requirements

## Error Handling

### Common Errors

1. **"Tool 'X' not found"**: The requested tool name doesn't exist
   - Check available tools with `GetLiveContext`
   - Verify the tool name spelling

2. **"Service handler cannot target all devices"**: Missing device name
   - Most intents require a `name` parameter
   - Specify which device to control

3. **"Device not found"**: The specified device doesn't exist or isn't exposed
   - Check device name spelling
   - Verify device is exposed to the assistant

### Error Response Format

Errors are returned as dictionaries with an "error" key:
```python
{"error": "Tool 'InvalidTool' not found. Available tools: HassTurnOn, HassGetState, ..."}
```

## Implementation Details

### Tool Registry

The `HAToolRegistry` class maintains:
- `api_instances`: Dict mapping API IDs to API instances
- `tools_by_name`: Dict mapping tool names to (tool, api_id) tuples

### Async Loading

Tool loading is async because:
- API instances may need to query the database
- Tool schemas may be dynamically generated
- Exposed entities need to be fetched

### Caching

- Tools are loaded once per agent creation
- Agents are cached per conversation and user
- Tool registry is recreated for each agent (ensures fresh tool list)

### LLM Context

The LLM context provides:
- User context (for permissions and personalization)
- Assistant configuration (which entities are exposed)
- Device ID (for location-aware intents)
- Language (for localized responses)

## Testing

### Manual Testing

1. Start Home Assistant with the integration configured
2. Open the conversation interface
3. Try commands like:
   - "Turn on the kitchen light"
   - "What's the temperature in the living room?"
   - "Show me all devices"

### Debugging

Enable debug logging:
```yaml
logger:
  default: info
  logs:
    homeassistant.components.bedrock_agent.ha_control_tool: debug
    homeassistant.components.bedrock_agent.strands_wrapper: debug
```

This will log:
- Tool loading and registration
- Tool calls with parameters
- Tool execution results
- Errors and exceptions

## Troubleshooting

### LLM not using the tool

**Symptoms**: LLM responds with text instead of controlling devices

**Solutions**:
1. Check that HA control is enabled (look for "Home Assistant control enabled" in logs)
2. Verify system prompt includes HA control instructions
3. Try more explicit commands: "Use the homeassistant_control tool to turn on the light"

### Tool calls failing

**Symptoms**: Tool is called but returns errors

**Solutions**:
1. Check device names match exactly (case-insensitive but spelling matters)
2. Verify devices are exposed to the assistant
3. Check logs for specific error messages
4. Try using `GetLiveContext` to see available devices

### Missing tools

**Symptoms**: Expected intents not available

**Solutions**:
1. Check that entities are exposed to the assistant
2. Verify the assistant configuration includes the required domains
3. Check that intent handlers are registered for those domains

## Future Improvements

Potential enhancements:
1. **Tool parameter schemas**: Expose full parameter schemas to the LLM
2. **Entity suggestions**: Provide entity name suggestions based on context
3. **Multi-device operations**: Support controlling multiple devices in one call
4. **Custom tool filtering**: Allow filtering which tools are exposed
5. **Tool usage analytics**: Track which tools are used most frequently
