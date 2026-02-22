# Bedrock Agent Test Suite

This test suite demonstrates the improved testability after reorganizing the component structure.

## Test Coverage

### conftest.py
Shared fixtures for all tests:
- `mock_config_entry`: Standard config entry for testing
- `mock_boto3_session`: Mocked boto3 session
- `mock_boto3_client`: Mocked boto3 client
- `mock_bedrock_model`: Mocked BedrockModel
- `mock_strands_agent`: Mocked strands Agent
- `mock_file_session_manager`: Mocked FileSessionManager
- `init_integration`: Fully initialized integration for testing

### test_init.py
Tests for integration setup and lifecycle:
- Setup entry success
- Unload entry
- Agent storage in hass.data
- Service registration

### test_agent.py
Tests for BedrockAgent conversation agent:
- Agent initialization
- Supported languages and models
- Conversation processing success
- Conversation ID generation
- Error handling

### test_strands_wrapper.py
Tests for StrandsAgentWrapper:
- Response generation success
- Client error handling
- Agent creation with different configurations
- LLM calling

### test_aws_client.py
Tests for AWSClientFactory:
- Bedrock agent client creation
- Boto3 session creation
- Credential handling

### test_image_processor.py
Tests for ImageProcessor:
- Image format conversion
- File loading success and failures
- Path validation
- MIME type validation
- URL loading success and failures
- HTTP error handling

### test_services.py
Tests for CognitiveTaskService:
- Text-only prompts
- Image file processing
- Image URL processing
- Client error handling

## Running Tests

```bash
# Run all bedrock_agent tests
pytest tests/components/bedrock_agent/

# Run specific test file
pytest tests/components/bedrock_agent/test_agent.py

# Run with coverage
pytest --cov=homeassistant.components.bedrock_agent tests/components/bedrock_agent/

# Update snapshots if needed
pytest --snapshot-update tests/components/bedrock_agent/
```

## Key Improvements

1. **Separation of Concerns**: Each module has focused responsibility
2. **Dependency Injection**: AWS factory and other dependencies are injected
3. **Mockable Components**: All external dependencies can be easily mocked
4. **Isolated Testing**: Each component can be tested independently
5. **Clear Fixtures**: Reusable fixtures reduce test boilerplate
6. **Comprehensive Coverage**: Tests cover success paths, error paths, and edge cases

## Test Patterns

### Using init_integration Fixture
```python
async def test_something(hass: HomeAssistant, init_integration: ConfigEntry):
    """Test with fully initialized integration."""
    agent = hass.data[DOMAIN][init_integration.entry_id]["agent"]
    # Test agent functionality
```

### Mocking AWS Calls
```python
async def test_aws_call(hass: HomeAssistant, mock_boto3_client: AsyncMock):
    """Test AWS client calls."""
    # mock_boto3_client is automatically used
    # Test your code
```

### Testing Error Handling
```python
async def test_error(hass: HomeAssistant):
    """Test error handling."""
    with pytest.raises(HomeAssistantError, match="Expected error"):
        # Code that should raise error
```
