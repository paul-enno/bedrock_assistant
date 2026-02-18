# Bedrock Agent Memory Functionality

## Overview

The Bedrock Agent integration now includes conversation memory functionality, allowing the agent to remember context across multiple interactions within the same conversation.

## How It Works

### Conversation-Based Memory

Each conversation is identified by a unique `conversation_id`. The agent maintains separate memory for each conversation:

- **Persistent Sessions**: Conversation history is stored using Strands' FileSessionManager
- **Automatic Caching**: Agents are cached per conversation for performance
- **Isolated Contexts**: Each conversation has its own independent memory

### Memory Storage

- **Location**: `/tmp/strands/` (configurable via `storage_dir`)
- **Format**: File-based session storage managed by Strands
- **Scope**: Per conversation ID

## Features

### 1. Automatic Memory

When you interact with the agent through the conversation interface, memory is automatically enabled:

```yaml
# Example conversation
User: "My name is John"
Agent: "Nice to meet you, John!"

# Later in the same conversation
User: "What's my name?"
Agent: "Your name is John."
```

### 2. Memory Management Services

#### Clear Specific Conversation Memory

Clear memory for a single conversation:

```yaml
service: bedrock_agent.clear_conversation_memory
data:
  conversation_id: "abc123"
```

#### Clear All Memory

Clear all conversation memories:

```yaml
service: bedrock_agent.clear_all_memory
```

## Configuration

### Enable/Disable Memory

Memory is enabled by default. To disable it, you would need to modify the wrapper initialization:

```python
StrandsAgentWrapper(
    hass=hass,
    aws_factory=aws_factory,
    model_id=model_id,
    apis=apis,
    system_prompt=system_prompt,
    enable_memory=False,  # Disable memory
)
```

### Custom Storage Location

Configure a custom storage directory:

```python
StrandsAgentWrapper(
    hass=hass,
    aws_factory=aws_factory,
    model_id=model_id,
    apis=apis,
    system_prompt=system_prompt,
    storage_dir="/config/bedrock_memory",  # Custom location
)
```

## Architecture

### Memory Flow

```
User Message
    │
    ▼
BedrockAgent.async_process()
    │
    ├─── conversation_id provided
    │    │
    │    ▼
    │    StrandsAgentWrapper.generate_response(conversation_id)
    │    │
    │    ▼
    │    get_agent_with_memory(conversation_id)
    │    │
    │    ├─── Agent cached? ──► Use cached agent
    │    │
    │    └─── Not cached ──► Create new agent with FileSessionManager
    │                        │
    │                        └─► Cache agent for future use
    │
    └─── No conversation_id ──► Use stateless agent
```

### Agent Caching

```python
# Internal cache structure
_agent_cache = {
    "conversation_id_1": Agent(session_manager=FileSessionManager("conversation_id_1")),
    "conversation_id_2": Agent(session_manager=FileSessionManager("conversation_id_2")),
    # ... more conversations
}
```

## API Reference

### StrandsAgentWrapper Methods

#### `get_agent_with_memory(conversation_id: str) -> Agent`

Get or create an agent with memory for a specific conversation.

**Parameters:**
- `conversation_id`: Unique identifier for the conversation

**Returns:**
- Agent instance with session manager for memory persistence

**Example:**
```python
agent = wrapper.get_agent_with_memory("user_123_conv_456")
response = agent("What did we discuss earlier?")
```

#### `clear_conversation_memory(conversation_id: str) -> None`

Clear memory for a specific conversation.

**Parameters:**
- `conversation_id`: Unique identifier for the conversation to clear

**Example:**
```python
wrapper.clear_conversation_memory("user_123_conv_456")
```

#### `clear_all_memory() -> None`

Clear all conversation memories.

**Example:**
```python
wrapper.clear_all_memory()
```

#### `generate_response(prompt, llm_context, conversation_id) -> str`

Generate a response with optional memory.

**Parameters:**
- `prompt`: The prompt to send to the agent
- `llm_context`: Optional LLM context
- `conversation_id`: Optional conversation ID for memory persistence

**Returns:**
- The agent's response as a string

**Example:**
```python
response = await wrapper.generate_response(
    "Tell me about yourself",
    llm_context=context,
    conversation_id="conv_123"
)
```

## Best Practices

### 1. Conversation ID Management

Use consistent conversation IDs:

```python
# Good: Use Home Assistant's conversation_id
conversation_id = user_input.conversation_id

# Bad: Random IDs each time
conversation_id = str(uuid.uuid4())  # Creates new conversation each time
```

### 2. Memory Cleanup

Periodically clear old conversations:

```yaml
# Automation to clear memory weekly
automation:
  - alias: "Clear Bedrock Memory Weekly"
    trigger:
      - platform: time
        at: "03:00:00"
    condition:
      - condition: time
        weekday:
          - sun
    action:
      - service: bedrock_agent.clear_all_memory
```

### 3. Storage Management

Monitor storage usage:

```bash
# Check memory storage size
du -sh /tmp/strands/

# Clean up if needed
rm -rf /tmp/strands/*
```

### 4. Privacy Considerations

- Memory is stored locally on disk
- Consider clearing sensitive conversations
- Implement retention policies for compliance

## Troubleshooting

### Memory Not Working

**Symptom**: Agent doesn't remember previous messages

**Solutions:**
1. Check that `conversation_id` is being passed
2. Verify `enable_memory=True` in wrapper
3. Check storage directory permissions
4. Review logs for errors

### Storage Issues

**Symptom**: Disk space warnings

**Solutions:**
1. Clear old conversations: `bedrock_agent.clear_all_memory`
2. Change storage location to larger partition
3. Implement automatic cleanup automation

### Performance Issues

**Symptom**: Slow responses with many conversations

**Solutions:**
1. Clear unused conversation memories
2. Limit number of cached agents
3. Consider implementing LRU cache eviction

## Examples

### Basic Conversation with Memory

```python
# First message
response1 = await wrapper.generate_response(
    "My favorite color is blue",
    conversation_id="user_123"
)

# Later message - agent remembers
response2 = await wrapper.generate_response(
    "What's my favorite color?",
    conversation_id="user_123"
)
# Response: "Your favorite color is blue."
```

### Stateless Request

```python
# No conversation_id = no memory
response = await wrapper.generate_response(
    "What's the weather?",
    conversation_id=None
)
```

### Memory Management

```python
# Clear specific conversation
wrapper.clear_conversation_memory("user_123")

# Clear all
wrapper.clear_all_memory()
```

## Technical Details

### Session Manager

Uses Strands' `FileSessionManager`:
- Stores conversation history in JSON format
- Automatically loads previous messages
- Maintains context window limits

### Agent Lifecycle

1. **First Request**: Create agent with session manager
2. **Subsequent Requests**: Reuse cached agent
3. **Memory Clear**: Remove from cache and delete session files

### Thread Safety

The implementation is thread-safe through Home Assistant's event loop:
- All operations run in the main event loop
- No concurrent access to agent cache
- File operations handled by Strands library

## Future Enhancements

Potential improvements:
1. Configurable memory retention periods
2. Conversation export/import
3. Memory compression for long conversations
4. Redis-based session storage for multi-instance setups
5. Conversation summarization for context window management
