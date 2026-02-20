# Bedrock Agent Test Improvements

## Summary

Updated the test suite to follow Home Assistant best practices, similar to the `openai_conversation` component tests. The tests now properly mock all external dependencies and can run without requiring actual AWS credentials or Bedrock access.

## Changes Made

### 1. Enhanced conftest.py

Added comprehensive mocking fixtures:

- **mock_boto3_session**: Mocks boto3.Session with proper bedrock-runtime client responses
- **mock_boto3_client**: Mocks boto3.client for config flow validation with proper ResponseMetadata
- **mock_bedrock_model**: Mocks the Strands BedrockModel
- **mock_strands_agent**: Mocks the Strands Agent with both async and sync call methods
- **mock_file_session_manager**: Mocks FileSessionManager for session persistence
- **mock_sliding_window_manager**: Mocks SlidingWindowConversationManager
- **mock_mem0_memory**: Mocks the mem0_memory tool
- **mock_llm_apis**: Mocks llm.async_get_apis to return empty list
- **mock_conversation_setup**: Mocks conversation component setup
- **mock_config_entry**: Provides a complete mock config entry with all options
- **mock_config_entry_with_memory**: Variant with memory enabled
- **init_integration**: Fixture that sets up the full integration for testing
- **setup_ha**: Auto-use fixture that sets up Home Assistant core

### 2. Created test_config_flow.py

Comprehensive config flow tests including:

- **test_form**: Tests the basic config flow form
- **test_form_invalid_auth**: Tests authentication error handling
- **test_form_cannot_connect**: Tests connection error handling
- **test_form_unknown_error**: Tests unknown error handling
- **test_options_flow**: Tests the options flow
- **test_options_flow_memory_disabled**: Tests that memory guidelines field is hidden when memory is disabled
- **test_options_flow_memory_enabled_shows_guidelines**: Tests that memory guidelines field appears when memory is enabled

### 3. Key Improvements

#### Proper Mocking
- All external dependencies (boto3, Strands SDK, mem0) are properly mocked
- Tests don't require actual AWS credentials
- Tests don't make real API calls
- Tests run quickly and reliably

#### Response Structure
- Mock responses include proper AWS ResponseMetadata
- Mock agent responses match the actual Strands Agent response structure
- Both async (`invoke_async`) and sync (`__call__`) agent methods are mocked

#### Comprehensive Coverage
- Config flow validation (success and error cases)
- Options flow with conditional fields
- Integration setup and teardown
- Service registration

## Benefits

1. **No External Dependencies**: Tests run without AWS credentials or internet connection
2. **Fast Execution**: Mocked responses are instant
3. **Reliable**: No flaky tests due to network issues or API rate limits
4. **Maintainable**: Clear fixtures make it easy to add new tests
5. **Best Practices**: Follows Home Assistant testing patterns

## Running the Tests

```bash
# Run all bedrock_agent tests
pytest tests/components/bedrock_agent/ -v

# Run specific test file
pytest tests/components/bedrock_agent/test_config_flow.py -v

# Run specific test
pytest tests/components/bedrock_agent/test_config_flow.py::test_form -xvs

# Run with coverage
pytest tests/components/bedrock_agent/ --cov=homeassistant.components.bedrock_agent
```

## Next Steps

Some existing tests may need updates to work with the new mocking approach:

1. **test_agent.py**: Update to use new fixtures
2. **test_services.py**: Update image processor mocks
3. **test_strands_wrapper.py**: Update to use new agent mocks
4. **test_aws_client.py**: Update boto3 mocks

The new conftest.py provides all the necessary fixtures - existing tests just need to be updated to use them properly.

## Example Test Pattern

```python
async def test_something(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_strands_agent: MagicMock,
) -> None:
    """Test something with the integration."""
    # Integration is already set up via init_integration fixture
    # All mocks are in place
    
    # Your test code here
    result = await hass.services.async_call(
        "bedrock_agent",
        "cognitive_task",
        {"prompt": "test"},
        blocking=True,
        return_response=True,
    )
    
    assert result["text"] == "Test response from agent"
```

## Notes

- The `setup_ha` fixture is auto-used, so Home Assistant core is always set up
- The `init_integration` fixture handles full integration setup with all mocks
- All mocks use proper context managers and are automatically cleaned up
- Mock responses match the actual API response structures
