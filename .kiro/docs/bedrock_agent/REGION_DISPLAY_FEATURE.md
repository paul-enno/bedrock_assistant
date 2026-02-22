# Region Display Feature - AI Configuration

## Overview

Added a read-only AWS Region field to the AI Configuration form so users can see which region is configured for their integration.

## Why This Matters

Users need to know which AWS region their integration is using because:
- Different regions have different model availability
- Pricing varies by region
- Latency depends on region proximity
- Some features may be region-specific

Previously, users had no way to see the configured region in the options flow.

## Implementation

### 1. Added Region Field to AI Config Form

The region field is displayed at the top of the AI Configuration form:

```python
ai_schema = vol.Schema({
    vol.Optional(
        CONST_REGION,
        description={"suggested_value": configured_region},
    ): selector.TextSelector(...),
    vol.Required(CONST_MODEL_ID, ...): ...,
    vol.Required(CONST_PROMPT_CONTEXT, ...): ...,
})
```

### 2. Read-Only Behavior

The field uses `vol.Optional` with `suggested_value` to display the region:
- Shows the current region value
- User can see but not effectively change it
- If user tries to change it, the value is filtered out on submit

### 3. Filter on Submit

When the form is submitted, the region value is removed:

```python
if user_input is not None:
    # Remove region from user_input if present (it's read-only)
    user_input.pop(CONST_REGION, None)
    # Update options with AI config
    self._options.update(user_input)
```

This ensures the region (which is in config entry data, not options) is not accidentally modified.

## User Experience

### AI Configuration Form

```
┌──────────────────────────────────────────────────────────────┐
│  AI CONFIGURATION                                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  AWS Region (Read-only)                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │ us-east-1                                          │    │
│  └────────────────────────────────────────────────────┘    │
│  The AWS region configured for this integration. To          │
│  change the region, you need to reconfigure the              │
│  integration.                                                │
│                                                              │
│  Model *                                                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Anthropic - Claude 3.5 Sonnet v2          ▼       │    │
│  └────────────────────────────────────────────────────┘    │
│  Select the AI model to use for conversations                │
│                                                              │
│  System Prompt *                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │ You are a helpful assistant...                     │    │
│  │                                                    │    │
│  └────────────────────────────────────────────────────┘    │
│  System prompt that defines the agent's behavior             │
│                                                              │
│                                    [Cancel]  [Submit]        │
└──────────────────────────────────────────────────────────────┘
```

### Field Details

**Label:** "AWS Region (Read-only)"
- Clear indication that this is informational only

**Description:** 
> "The AWS region configured for this integration. To change the region, you need to reconfigure the integration."
- Explains why it's read-only
- Tells users how to change it if needed

**Value:** Shows the actual configured region (e.g., "us-east-1")

## Technical Details

### Region Source

The region is retrieved from the config entry data:

```python
configured_region = self.config_entry.data.get(CONST_REGION, "Unknown")
```

Config entry data is immutable (set during initial setup), while options are mutable (can be changed in options flow).

### Why Read-Only?

The region is part of the AWS credentials configuration and cannot be changed without:
1. Creating new AWS clients
2. Reloading available models
3. Potentially affecting authentication

Therefore, changing the region requires reconfiguring the entire integration.

### Data Flow

```
Initial Setup:
  User enters credentials + region
  ↓
  Stored in config_entry.data (immutable)
  ↓
  Used to create AWS clients

Options Flow:
  Display region from config_entry.data
  ↓
  User sees region (read-only)
  ↓
  User configures model/prompt
  ↓
  Only model/prompt saved to config_entry.options
```

## Strings Configuration

Added to `strings.json`:

```json
{
  "options": {
    "step": {
      "ai_config": {
        "data": {
          "region": "AWS Region (Read-only)",
          "model_id": "Model",
          "prompt_context": "System Prompt"
        },
        "data_description": {
          "region": "The AWS region configured for this integration. To change the region, you need to reconfigure the integration.",
          "model_id": "Select the AI model to use for conversations...",
          "prompt_context": "System prompt that defines the agent's behavior..."
        }
      }
    }
  }
}
```

## Benefits

### For Users

1. **Visibility**: Can see which region is configured
2. **Context**: Understand why certain models are available
3. **Troubleshooting**: Easier to diagnose region-related issues
4. **Clarity**: Clear indication that region cannot be changed here

### For Support

1. **Debugging**: Users can report their configured region
2. **Documentation**: Can reference region in troubleshooting guides
3. **Validation**: Confirm users are using the correct region

## Testing

All tests pass with the new field:
- ✅ 44/44 tests passing (100%)
- ✅ MyPy type checking passes
- ✅ Config flow tests pass
- ✅ Region field is displayed correctly
- ✅ Region value is filtered out on submit

## Future Enhancements

Potential improvements:
1. Add region icon/flag for visual identification
2. Show region-specific information (available models, pricing)
3. Add link to AWS console for the specific region
4. Show latency estimate based on user location

## Comparison with Other Integrations

Many Home Assistant integrations show read-only configuration information:
- **Hue Bridge**: Shows bridge IP address
- **MQTT**: Shows broker address
- **HomeKit**: Shows pairing code

This follows the same pattern of displaying immutable configuration data for user reference.

## Summary

**What was added:**
- Read-only AWS Region field in AI Configuration form
- Clear labeling as "(Read-only)"
- Helpful description explaining how to change it
- Automatic filtering to prevent accidental modification

**Why it matters:**
- Users can see their configured region
- Provides context for model availability
- Helps with troubleshooting
- Follows Home Assistant patterns

**Result:**
- ✅ Better user visibility
- ✅ Clear and informative
- ✅ All tests pass
- ✅ Follows best practices
