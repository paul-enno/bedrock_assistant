# Bedrock Agent Refactoring Guide

## Overview

The component has been reorganized to improve testability and maintainability by separating concerns into focused modules.

## New Structure

```
homeassistant/components/bedrock_agent/
├── __init__.py              # Minimal entry point
├── agent.py                 # BedrockAgent conversation agent
├── strands_wrapper.py       # Strands library wrapper
├── aws_client.py            # AWS client factory
├── image_processor.py       # Image handling utilities
├── services.py              # Service handlers
├── config_flow.py           # Unchanged
└── const.py                 # Unchanged
```

## Key Changes

### 1. AWS Client Factory (aws_client.py)
**Purpose**: Centralize AWS client creation with proper async handling

**Benefits**:
- Single source of truth for AWS credentials
- Easy to mock in tests
- Reusable across components

**Usage**:
```python
factory = AWSClientFactory(hass, key_id, key_secret, region)
client = await factory.create_bedrock_agent_client()
session = factory.create_boto3_session()
```

### 2. Image Processor (image_processor.py)
**Purpose**: Handle all image loading and validation

**Benefits**:
- Isolated image processing logic
- Comprehensive error handling
- Easy to test independently

**Features**:
- File path validation
- MIME type checking
- URL fetching
- Bedrock format conversion

### 3. Service Handlers (services.py)
**Purpose**: Separate service logic from setup

**Benefits**:
- Cleaner __init__.py
- Testable service handlers
- Clear service boundaries

**Pattern**:
```python
service = CognitiveTaskService(hass, bedrock_agent)
hass.services.async_register(
    DOMAIN,
    "cognitive_task",
    service.async_handle_cognitive_task,
    schema=COGNITIVE_TASK_SCHEMA,
)
```

### 4. Conversation Agent (agent.py)
**Purpose**: Extract BedrockAgent from __init__.py

**Benefits**:
- Focused responsibility
- Easier to test
- Clear agent lifecycle

**Changes**:
- Uses AWSClientFactory for client creation
- Cleaner separation of agent vs custom agent logic
- Better error handling

### 5. Strands Wrapper (strands_wrapper.py)
**Purpose**: Improved wrapper with dependency injection

**Benefits**:
- No direct boto3 calls
- Configurable session management
- Testable agent creation

**Improvements**:
- Uses AWSClientFactory instead of direct credentials
- Configurable storage_dir (no hardcoded /tmp/strands)
- Configurable session_id (no hardcoded "enno-123")
- Cleaner get_agent method with kwargs

## Migration Impact

### Breaking Changes
None - all changes are internal refactoring

### API Changes
None - public interfaces remain the same

### Configuration Changes
None - config entry structure unchanged

## Testing Improvements

### Before Refactoring
- Difficult to mock boto3 clients
- Hard to test image processing separately
- Service logic mixed with setup
- Hardcoded values made testing brittle

### After Refactoring
- Each module independently testable
- Clear mock points for dependencies
- Comprehensive test fixtures
- No hardcoded values in production code

### Test Coverage Areas
1. Integration setup/teardown
2. Agent conversation processing
3. Strands wrapper functionality
4. AWS client creation
5. Image processing (files and URLs)
6. Service handlers
7. Error handling throughout

## Best Practices Applied

### Dependency Injection
```python
# Before
class StrandsAgentWrapper:
    def __init__(self, hass, key_id, key_secret, region, ...):
        self.aws_access_key_id = key_id
        # Direct boto3 calls

# After
class StrandsAgentWrapper:
    def __init__(self, hass, aws_factory, ...):
        self.aws_factory = aws_factory
        # Use factory for boto3
```

### Separation of Concerns
```python
# Before: Everything in __init__.py
async def async_setup_entry(...):
    # Agent creation
    # Service registration
    # Image processing
    # AWS client setup

# After: Focused modules
async def async_setup_entry(...):
    agent = BedrockAgent(hass, entry)
    service = CognitiveTaskService(hass, agent)
    # Clean setup
```

### Configurable Defaults
```python
# Before
session_manager = FileSessionManager(
    session_id="enno-123",  # Hardcoded
    storage_dir="/tmp/strands"  # Hardcoded
)

# After
session_manager = FileSessionManager(
    session_id=self.session_id or "default-session",
    storage_dir=self.storage_dir  # Configurable
)
```

## Future Improvements

### Potential Enhancements
1. Use conversation_id for session_id
2. User-specific session isolation
3. Configurable storage directory via options
4. Dynamic model list from Bedrock API
5. Streaming support in strands wrapper
6. Tool/API integration in strands wrapper

### Testing Enhancements
1. Integration tests with real AWS (optional)
2. Snapshot tests for responses
3. Performance tests for image processing
4. Load tests for concurrent requests

## Rollback Plan

If issues arise, the old structure can be restored by:
1. Reverting to previous __init__.py
2. Removing new module files
3. No config entry migration needed

## Validation

Run the following to validate the refactoring:

```bash
# Type checking
mypy homeassistant/components/bedrock_agent

# Linting
pylint homeassistant/components/bedrock_agent

# Tests
pytest tests/components/bedrock_agent/

# Integration test (if available)
pytest tests/components/bedrock_agent/ --integration
```
