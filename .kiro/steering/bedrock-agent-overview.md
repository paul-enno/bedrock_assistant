---
inclusion: fileMatch
fileMatchPattern: 'homeassistant/components/bedrock_agent/**'
---

# Amazon Bedrock Agent Integration - Development Guide

This integration provides Home Assistant with AI conversation capabilities powered by Amazon Bedrock, supporting both foundation models and custom agents.

## Architecture Overview

The integration consists of several key components:

- **BedrockAgent**: Main conversation agent implementing `AbstractConversationAgent`
- **StrandsAgentWrapper**: Wrapper around the strands library for agent management
- **Config Flow**: Multi-step configuration for AWS credentials and model selection
- **Cognitive Task Service**: Multimodal service supporting text and image inputs

## Key Files

- `__init__.py`: Entry point, agent setup, service registration
- `config_flow.py`: Configuration and options flow handlers
- `strands_wrapper.py`: Strands library integration wrapper
- `const.py`: Constants and model lists
- `services.yaml`: Service definitions
- `strings.json`: Localization strings

## Configuration Structure

### Config Entry Data (Immutable)
- `key_id`: AWS access key ID
- `key_secret`: AWS secret access key
- `region`: AWS region
- `title`: User-defined integration name

### Config Entry Options (Mutable)
- `model_id`: Selected foundation model or inference profile
- `prompt_context`: System prompt prefix
- `knowledgebase_id`: Optional Bedrock knowledge base
- `agent_id`: Optional Bedrock agent
- `agent_alias_id`: Agent alias (defaults to "TSTALIASID")

## AWS Integration Patterns

### Boto3 Client Creation
Always use `async_add_executor_job` with `partial` for boto3 client creation:

```python
bedrock_client = await hass.async_add_executor_job(
    partial(
        boto3.client,
        service_name="bedrock",
        region_name=region,
        aws_access_key_id=key_id,
        aws_secret_access_key=key_secret
    )
)
```

### Boto3 API Calls
Wrap all boto3 API calls in executor jobs:

```python
response = await hass.async_add_executor_job(
    partial(
        client.list_foundation_models,
        byOutputModality="TEXT",
        byInferenceType="ON_DEMAND"
    )
)
```

## Conversation Agent Implementation

### Agent Lifecycle
1. Agent initialized in `async_setup_entry`
2. Registered with `conversation.async_set_agent`
3. Unregistered in `async_unload_entry`

### Processing Flow
1. User input received via `async_process`
2. Conversation ID generated or reused
3. Request routed to either:
   - Bedrock Agent (if `agent_id` configured)
   - Strands wrapper (for foundation models)
4. Response formatted as `IntentResponse`

### Error Handling
Use specific exception types:
- `ConfigEntryNotReady`: Temporary connection issues
- `ConfigEntryAuthFailed`: Authentication failures
- `HomeAssistantError`: General runtime errors

## Strands Library Integration

### Agent Creation
The wrapper creates strands agents with:
- BedrockModel configured with boto3 session
- FileSessionManager for conversation persistence
- Optional system prompt
- Streaming disabled for compatibility

### Session Management
- Sessions stored in `/tmp/strands` (temporary)
- Session ID currently hardcoded (consider using conversation_id)
- Session manager optional for stateless requests

## Cognitive Task Service

### Purpose
Multimodal service for image analysis and description using Claude models.

### Input Handling
- Text prompts (required)
- Image filenames (optional, validated against allowlist)
- Image URLs (optional, fetched and validated)

### Image Processing
1. Validate file paths with `hass.config.is_allowed_path`
2. Check file existence and MIME type
3. Load images using `PIL.Image.open` in executor
4. Convert to Bedrock format with `build_converse_prompt_content`

### Response Format
Returns ServiceResponse with `{"text": "description"}`

## Config Flow Best Practices

### Multi-Step Flow
1. **User Step**: Collect AWS credentials and validate connection
2. **Model Config Step**: Load available resources and configure model

### Dynamic Options Loading
- Foundation models: `list_foundation_models` + `list_inference_profiles`
- Knowledge bases: `list_knowledge_bases`
- Agents: `list_agents`

### Selector Patterns
Use `SelectSelector` with `SelectOptionDict` for dynamic options:

```python
selector.SelectSelector(
    selector.SelectSelectorConfig(options=[
        selector.SelectOptionDict({
            "value": item_id,
            "label": item_name
        })
        for item in items
    ])
)
```

### Options Flow
- Reload dynamic options on each display
- Use `suggested_value` for optional fields
- Support multiline text for prompts

## Testing Considerations

### Mocking AWS Services
- Mock boto3 clients and responses
- Test connection validation errors
- Verify executor job wrapping

### Config Flow Testing
- Test validation errors (cannot_connect, invalid_auth)
- Verify multi-step flow progression
- Test options flow updates

### Service Testing
- Mock image loading and processing
- Test file path validation
- Verify error handling for invalid inputs

## Common Patterns

### Bare Exception Usage
Allowed in config flow for robustness:

```python
async def async_step_user(self, user_input):
    try:
        await validate_input(self.hass, user_input)
    except CannotConnect:
        errors["base"] = "cannot_connect"
    except InvalidAuth:
        errors["base"] = "invalid_auth"
    except Exception:  # ✅ Allowed in config flow
        errors["base"] = "unknown"
```

### Executor Job Patterns
Always wrap blocking I/O:

```python
# Image loading
image = await hass.async_add_executor_job(PIL.Image.open, filename)

# URL fetching
opened_url = await hass.async_add_executor_job(urlopen, url)

# Boto3 calls
response = await hass.async_add_executor_job(client.method, args)
```

### Logging
- Use lazy logging: `_LOGGER.debug("Message with %s", variable)`
- No periods at end of messages
- No sensitive data (keys, tokens)
- Set strands logger to ERROR level to reduce noise

## Known Issues and TODOs

### Session Management
- Session ID currently hardcoded as "enno-123"
- Should use `conversation_id` from user input
- Consider user-specific session isolation

### Agent Initialization
- Commented-out code in `__init__.py` for bedrock_agent client
- Consider cleanup of unused initialization patterns

### Model List Maintenance
- `CONST_MODEL_LIST` in const.py may become outdated
- Consider dynamic loading from Bedrock API
- Inference profiles now supported alongside foundation models

## Dependencies

- `boto3==1.39.9`: AWS SDK
- `botocore==1.39.9`: AWS SDK core
- `strands-agents==1.26.0`: Agent framework
- `PIL`: Image processing

## Integration Type

- **Type**: service
- **IoT Class**: cloud_push
- **Dependencies**: conversation, assist_pipeline
- **Codeowner**: @paul-enno
