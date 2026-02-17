# Bedrock Agent Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Assistant Core                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    __init__.py (Entry Point)                 │
│  - async_setup_entry()                                       │
│  - async_unload_entry()                                      │
│  - options_update_listener()                                 │
└──────┬──────────────────────────────────┬───────────────────┘
       │                                   │
       ▼                                   ▼
┌─────────────────┐              ┌──────────────────────┐
│   agent.py      │              │    services.py       │
│  BedrockAgent   │              │ CognitiveTaskService │
└────┬────────────┘              └──────┬───────────────┘
     │                                   │
     │ uses                              │ uses
     ▼                                   ▼
┌──────────────────────┐        ┌──────────────────────┐
│ strands_wrapper.py   │        │ image_processor.py   │
│ StrandsAgentWrapper  │        │  ImageProcessor      │
└────┬─────────────────┘        └──────────────────────┘
     │
     │ uses
     ▼
┌──────────────────────┐
│   aws_client.py      │
│  AWSClientFactory    │
└──────────────────────┘
```

## Data Flow

### Conversation Processing

```
User Input
    │
    ▼
BedrockAgent.async_process()
    │
    ├─── Has custom agent? ──► async_call_bedrock_agent()
    │                               │
    │                               ▼
    │                          AWS Bedrock Agent API
    │
    └─── Foundation model ──► StrandsAgentWrapper.generate_response()
                                   │
                                   ▼
                              Strands Agent
                                   │
                                   ▼
                              AWS Bedrock API
```

### Cognitive Task Service

```
Service Call
    │
    ▼
CognitiveTaskService.async_handle_cognitive_task()
    │
    ├─── Text Prompt ──────────────┐
    │                               │
    ├─── Image Files ──► ImageProcessor.load_image_from_file()
    │                               │
    ├─── Image URLs ───► ImageProcessor.load_image_from_url()
    │                               │
    └───────────────────────────────┴──► Strands Agent
                                              │
                                              ▼
                                         AWS Bedrock API
```

## Module Responsibilities

### __init__.py
- Integration entry point
- Config entry setup/teardown
- Service registration
- Agent registration with conversation component

### agent.py (BedrockAgent)
- Implements AbstractConversationAgent
- Handles conversation processing
- Routes to custom agents or foundation models
- Manages conversation history
- Error handling for conversation flow

### strands_wrapper.py (StrandsAgentWrapper)
- Wraps strands library
- Creates and manages strands agents
- Handles different agent configurations
- Provides LLM calling interface
- Session management

### aws_client.py (AWSClientFactory)
- Creates AWS clients (boto3)
- Manages AWS credentials
- Provides boto3 sessions
- Centralizes AWS configuration

### image_processor.py (ImageProcessor)
- Loads images from files
- Loads images from URLs
- Validates file paths
- Validates MIME types
- Converts images to Bedrock format

### services.py (CognitiveTaskService)
- Handles cognitive_task service
- Processes multimodal inputs
- Coordinates image processing
- Formats service responses

## Dependency Graph

```
__init__.py
    ├── agent.py
    │   ├── aws_client.py
    │   └── strands_wrapper.py
    │       └── aws_client.py
    └── services.py
        ├── agent.py (reference)
        └── image_processor.py
```

## Testing Strategy

### Unit Tests (Isolated)
```
test_aws_client.py
    └── Tests AWSClientFactory in isolation

test_image_processor.py
    └── Tests ImageProcessor with mocked file system

test_strands_wrapper.py
    └── Tests StrandsAgentWrapper with mocked AWS

test_agent.py
    └── Tests BedrockAgent with mocked dependencies

test_services.py
    └── Tests CognitiveTaskService with mocked components
```

### Integration Tests
```
test_init.py
    └── Tests full integration setup with all components
```

## Configuration Flow

```
Config Entry
    │
    ├── data (immutable)
    │   ├── key_id
    │   ├── key_secret
    │   ├── region
    │   └── title
    │
    └── options (mutable)
        ├── model_id
        ├── prompt_context
        ├── knowledgebase_id (optional)
        ├── agent_id (optional)
        └── agent_alias_id (optional)
```

## Error Handling Flow

```
User Request
    │
    ▼
Try: Process Request
    │
    ├── ConfigEntryNotReady ──► Temporary failure, retry later
    │
    ├── ConfigEntryAuthFailed ──► Auth issue, reconfigure
    │
    ├── HomeAssistantError ──► General error, show to user
    │
    └── ClientError (boto3) ──► Wrap in HomeAssistantError
```

## Extension Points

### Adding New Services
1. Create service handler in services.py
2. Register in __init__.py
3. Add schema validation
4. Add tests in test_services.py

### Adding New Models
1. Update CONST_MODEL_LIST in const.py
2. Test with existing infrastructure
3. No code changes needed

### Adding Tool Support
1. Extend StrandsAgentWrapper
2. Add tool registration
3. Update agent initialization
4. Add tool-specific tests

### Adding Streaming
1. Update StrandsAgentWrapper.get_agent()
2. Add streaming response handler
3. Update agent.py to handle streams
4. Add streaming tests
