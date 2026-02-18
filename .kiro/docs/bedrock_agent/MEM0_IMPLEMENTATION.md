# Mem0 Memory Implementation

## Overview

The Bedrock Agent integration now uses **Mem0.ai** for long-term semantic memory. This provides intelligent memory capabilities that persist across all conversations and enable personalized, context-aware responses.

## What is Mem0?

Mem0 is a semantic memory layer that:
- **Stores information intelligently** - Automatically extracts and stores important facts, preferences, and context
- **Retrieves by meaning** - Finds relevant memories based on semantic similarity, not just keywords
- **Persists across conversations** - Memories are available in all future conversations
- **Works automatically** - The agent decides when to store and retrieve memories

## Key Features

### 1. Automatic Memory Storage
When users share important information, the agent automatically stores it:

```
User: "I prefer vegetarian food"
Agent: [Stores preference in mem0]
Agent: "Got it! I'll remember that you prefer vegetarian food."
```

### 2. Semantic Retrieval
The agent retrieves relevant memories based on meaning:

```
User: "What should I cook for dinner?"
Agent: [Retrieves vegetarian preference from mem0]
Agent: "Based on your preference for vegetarian food, how about a nice pasta primavera?"
```

### 3. Cross-Conversation Memory
Memories persist across all conversations:

```
# Conversation 1 (Monday)
User: "I have a dog named Max"

# Conversation 2 (Friday)
User: "What pets do I have?"
Agent: [Retrieves memory from Monday]
Agent: "You have a dog named Max!"
```

### 4. User Isolation
Each Home Assistant config entry has its own memory space, ensuring privacy and preventing memory leakage between different setups.

## Installation

The mem0 dependency is automatically installed with the integration:

```bash
pip install 'strands-agents-tools[mem0_memory]==0.1.19'
pip install faiss-cpu==1.9.0
```

If you see a warning about mem0 or faiss not being available, install them manually:

```bash
pip install 'strands-agents-tools[mem0_memory]'
pip install faiss-cpu
```

### Why faiss-cpu?

Mem0 uses FAISS (Facebook AI Similarity Search) for efficient semantic search and vector similarity operations. This is what enables the intelligent memory retrieval by meaning rather than keywords.

## Configuration

### Memory is Enabled by Default

Memory is automatically enabled when:
1. The `strands-agents-tools[mem0_memory]` package is installed
2. The `faiss-cpu` package is installed
3. The integration is set up

### AWS Credentials for Mem0

Mem0 uses AWS Bedrock for:
- **Embeddings**: Converting text to vectors (amazon.titan-embed-text-v2:0)
- **LLM Operations**: Processing and extracting memories (anthropic.claude-3-5-haiku-20241022-v1:0)

The integration automatically configures mem0 with your AWS credentials:
- Uses the same AWS credentials from your Bedrock Agent config entry
- Sets environment variables for mem0 to use
- Configures Bedrock as the provider for embeddings and LLM

**No additional configuration needed!** The integration handles everything automatically.

### User Identification

The integration uses Home Assistant's user context for memory isolation:

**User ID Source**: `context.user_id` from the conversation context
- Each Home Assistant user has their own memory space
- Memories are isolated between different users
- Same user gets consistent memory across all conversations
- Falls back to config entry ID if user context is not available

**Benefits**:
- ✅ True multi-user support
- ✅ Privacy between users
- ✅ Personalized memories per user
- ✅ Works with Home Assistant authentication

## How It Works

### AWS Credentials Configuration

The integration automatically configures mem0 to use your AWS Bedrock credentials:

1. **Credentials from Config Entry**: Uses the same AWS credentials you configured for the Bedrock Agent
2. **Environment Variables**: Sets AWS environment variables for mem0 to use
3. **Bedrock Providers**: Configures mem0 to use Bedrock for embeddings and LLM operations

**Models Used by Mem0:**
- **Embeddings**: `amazon.titan-embed-text-v2:0` (converts text to vectors)
- **LLM**: `anthropic.claude-3-5-haiku-20241022-v1:0` (processes and extracts memories)

These models are automatically configured and use your existing AWS Bedrock access.

### System Prompt Enhancement

When memory is enabled, the agent's system prompt is automatically enhanced with memory instructions:

```
You have access to a long-term memory system that persists across conversations. Use the memory tool to:
- Store important information about the user (preferences, facts, context)
- Retrieve relevant memories to provide personalized responses
- Remember user preferences and past interactions

When users share important information, proactively store it in memory. When answering questions, retrieve relevant memories to provide contextual, personalized responses.
```

### Agent Caching

The wrapper caches agent instances per conversation and user:
- Cache key: `{conversation_id}_{user_id}`
- First request creates agent (slower)
- Subsequent requests reuse agent (faster)
- Cache cleared on service call or restart
- Each user gets their own cached agents

### Memory Tool Usage

The agent automatically uses the mem0_memory tool to:

1. **Store memories**:
   ```python
   mem0_memory(
       action="store",
       user_id="config_entry_id",
       content="User prefers vegetarian food"
   )
   ```

2. **Retrieve memories**:
   ```python
   mem0_memory(
       action="retrieve",
       user_id="config_entry_id",
       query="food preferences"
   )
   ```

3. **List all memories**:
   ```python
   mem0_memory(
       action="list",
       user_id="config_entry_id"
   )
   ```

## Services

### get_memory_stats

Get statistics about the memory system:

```yaml
service: bedrock_agent.get_memory_stats
```

Returns:
```json
{
  "memory_enabled": true,
  "mem0_available": true,
  "user_id": "abc123...",
  "cached_conversations": 3,
  "tools_count": 1
}
```

### clear_conversation_cache

Clear the agent cache for a specific conversation:

```yaml
service: bedrock_agent.clear_conversation_cache
data:
  conversation_id: "conversation_123"
```

**Note**: This only clears the agent instance cache, not the mem0 memories. Memories persist in mem0's storage.

### clear_all_cache

Clear all agent caches:

```yaml
service: bedrock_agent.clear_all_cache
```

**Note**: This only clears agent instance caches, not mem0 memories.

## Memory Storage

### Where Memories are Stored

Mem0 stores memories in its own storage backend. By default, this is:
- **Local storage**: `~/.mem0/` directory
- **Cloud storage**: Optional, requires mem0 API key

### Memory Persistence

Memories persist:
- ✅ Across Home Assistant restarts
- ✅ Across conversation sessions
- ✅ Across different conversation IDs
- ✅ Until explicitly deleted via mem0 API

### Clearing Mem0 Memories

To clear actual mem0 memories (not just cache), you need to use the mem0 API directly or ask the agent to delete specific memories.

## Example Interactions

### Storing Preferences

```
User: "Remember that I like to keep the house at 72°F"
Agent: "I'll remember that you prefer to keep the house at 72°F."
```

### Retrieving Context

```
User: "What temperature do I like?"
Agent: "You prefer to keep the house at 72°F."
```

### Personalized Responses

```
User: "Should I turn on the heater?"
Agent: "Since you prefer to keep the house at 72°F, I'd recommend turning on the heater if the current temperature is below that."
```

### Cross-Conversation Memory

```
# Monday morning
User: "I'm going on vacation next week"

# Friday afternoon
User: "What's happening next week?"
Agent: "You mentioned you're going on vacation next week!"
```

## Troubleshooting

### Memory Not Working

1. **Check if mem0 is available**:
   ```yaml
   service: bedrock_agent.get_memory_stats
   ```
   
   Look for `"mem0_available": true`

2. **Check logs** for warnings:
   ```
   WARNING: mem0_memory tool not available. Install with: pip install 'strands-agents-tools[mem0_memory]'
   WARNING: mem0_memory tool requires faiss-cpu. Install with: pip install faiss-cpu
   ```

3. **Check the error field** in memory stats:
   ```json
   {
     "mem0_available": false,
     "error": "faiss-cpu not available. Install with: pip install faiss-cpu"
   }
   ```

4. **Reinstall the packages**:
   ```bash
   pip install --force-reinstall 'strands-agents-tools[mem0_memory]'
   pip install faiss-cpu
   ```

### Agent Not Storing Memories

The agent decides when to store memories based on the conversation context. To explicitly store information:

```
User: "Remember that I prefer vegetarian food"
```

Use explicit language like "remember", "note that", or "I want you to know".

### Memory Retrieval Issues

If the agent isn't retrieving relevant memories:
1. Check that memories were actually stored
2. Try more specific queries
3. The agent uses semantic search, so related concepts should work

## Performance Considerations

### Agent Caching

- Agents are cached per conversation ID
- First request creates agent (slower)
- Subsequent requests reuse agent (faster)
- Cache cleared on service call or restart

### Memory Operations

- Memory storage: ~100-200ms per operation
- Memory retrieval: ~200-500ms depending on memory count
- Semantic search: Scales well with memory count

### AWS Bedrock Costs

Mem0 uses AWS Bedrock for embeddings and LLM operations, which incurs costs:

**Per Memory Operation:**
- **Embedding**: ~$0.0001 per memory (Titan Embeddings v2)
- **LLM Processing**: ~$0.001 per memory (Claude 3.5 Haiku)

**Typical Usage:**
- Storing 1 memory: ~$0.0011
- Retrieving memories: ~$0.0001 per search
- 100 memories/day: ~$0.11/day or ~$3.30/month

**Cost Optimization:**
- Memories are cached locally in FAISS
- Retrieval uses local vector search (no Bedrock cost)
- LLM only called for memory extraction/processing
- Embeddings only generated once per memory

**Note**: These are approximate costs. Actual costs depend on:
- Memory content length
- Number of operations
- AWS region pricing
- Your AWS pricing tier

## Privacy and Security

### User Isolation

Each config entry has isolated memory:
- Entry ID used as user identifier
- No memory sharing between entries
- Safe for multi-user Home Assistant setups

### Data Storage

- Memories stored locally by default
- No data sent to external services (unless using mem0 cloud)
- Can be self-hosted for complete control

### Sensitive Information

The agent is instructed to store user information, but you should:
- Avoid sharing sensitive credentials
- Review stored memories periodically
- Use mem0 API to delete sensitive memories if needed

## Advanced Usage

### Custom Memory Operations

You can ask the agent to perform specific memory operations:

```
User: "Show me all my memories"
Agent: [Lists all stored memories]

User: "Forget about my food preferences"
Agent: [Deletes relevant memories]
```

### Memory Management

For programmatic memory management, use the mem0 Python API directly:

```python
from mem0 import Memory

memory = Memory()

# List all memories for a user
memories = memory.get_all(user_id="config_entry_id")

# Delete a specific memory
memory.delete(memory_id="memory_123")

# Search memories
results = memory.search(query="food preferences", user_id="config_entry_id")
```

## Migration from FileSessionManager

The previous implementation used `FileSessionManager` for basic conversation history. The new mem0 implementation provides:

| Feature | FileSessionManager | Mem0 |
|---------|-------------------|------|
| Conversation history | ✅ Yes | ✅ Yes |
| Semantic search | ❌ No | ✅ Yes |
| Long-term memory | ❌ No | ✅ Yes |
| Preference learning | ❌ No | ✅ Yes |
| Fact extraction | ❌ No | ✅ Yes |
| Cross-conversation | ❌ No | ✅ Yes |

### No Migration Needed

The new implementation works immediately - no migration of old data is required. The agent will start building new memories from the first conversation.

## Future Enhancements

Potential future improvements:
1. **Memory analytics** - Dashboard showing stored memories
2. **Memory export** - Export memories for backup
3. **Memory import** - Import memories from other sources
4. **Memory categories** - Organize memories by type
5. **Memory expiration** - Auto-delete old memories
6. **Multi-user support** - Map Home Assistant users to mem0 users

## Resources

- **Mem0 Documentation**: https://docs.mem0.ai
- **Strands Tools**: https://github.com/strands-agents/tools
- **Community Support**: https://github.com/strands-agents/tools/issues
