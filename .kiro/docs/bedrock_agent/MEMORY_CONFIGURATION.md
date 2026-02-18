# Memory Configuration Option

## Overview

The Bedrock Agent integration now includes a configuration option to enable or disable long-term memory functionality. This gives users control over whether they want semantic memory features.

## Configuration Location

The memory option is available in two places:

1. **Initial Setup**: During integration setup (modelconfig step)
2. **Options Flow**: In integration settings (can be changed anytime)

## How to Configure

### During Initial Setup

When adding a new Bedrock Agent integration:

1. Enter AWS credentials (step 1)
2. Configure model settings (step 2)
3. Check/uncheck "Enable Long-term Memory" checkbox
4. Complete setup

**Default**: Memory is ENABLED by default

### After Setup (Options Flow)

To change memory settings for existing integration:

1. Go to Settings → Devices & Services
2. Find "Amazon Bedrock Agent"
3. Click "Configure" on your integration
4. Check/uncheck "Enable Long-term Memory"
5. Click "Submit"

**Note**: Changes take effect immediately (no restart required)

## What the Option Does

### When ENABLED (checked)

✅ **Long-term semantic memory active**:
- Agent remembers information across conversations
- Memories persist for each user
- Semantic search for relevant context
- Personalized responses based on history
- Uses mem0 with AWS Bedrock

**Requirements**:
- `strands-agents-tools[mem0_memory]` installed
- `faiss-cpu` installed
- AWS Bedrock access for embeddings/LLM

**Behavior**:
```python
enable_memory = True
# Agent has mem0_memory tool
# Stores and retrieves memories
# Enhanced system prompt with memory instructions
```

### When DISABLED (unchecked)

❌ **Memory functionality disabled**:
- No long-term memory
- Each conversation is independent
- No memory storage or retrieval
- Standard agent without memory tool
- No AWS Bedrock calls for memory

**Behavior**:
```python
enable_memory = False
# Agent has no mem0_memory tool
# No memory operations
# Standard system prompt
```

## Use Cases

### Enable Memory When:

1. **Personal Assistant**: User wants personalized responses
2. **Home Automation**: Remember user preferences
3. **Multi-User Home**: Each user needs their own memory
4. **Long-term Context**: Conversations build on past interactions
5. **Preference Learning**: Agent learns user habits

### Disable Memory When:

1. **Privacy Concerns**: Don't want conversations remembered
2. **Temporary Use**: Guest or temporary setup
3. **Cost Optimization**: Avoid Bedrock memory costs
4. **Simple Queries**: Don't need context
5. **Testing**: Want clean slate for each conversation

## Technical Details

### Configuration Storage

The option is stored in config entry options:

```python
# In config_flow.py
vol.Optional(
    CONST_ENABLE_MEMORY,
    default=True,
): selector.BooleanSelector()

# In agent.py
enable_memory = self.entry.options.get(CONST_ENABLE_MEMORY, True)
```

### Wrapper Initialization

The option is passed to StrandsAgentWrapper:

```python
self.strands_agent_wrapper = StrandsAgentWrapper(
    hass=self.hass,
    aws_factory=self.aws_factory,
    model_id=self.entry.options[CONST_MODEL_ID],
    apis=llm.async_get_apis(self.hass),
    system_prompt=self.entry.options[CONST_PROMPT_CONTEXT],
    user_id=entry.entry_id,
    enable_memory=self.entry.options.get(CONST_ENABLE_MEMORY, True),
)
```

### Memory Availability Check

The wrapper checks both the option AND mem0 availability:

```python
self.enable_memory = enable_memory and MEM0_AVAILABLE
```

This ensures:
- If option is disabled → memory disabled
- If option is enabled but mem0 not available → memory disabled with warning
- If option is enabled and mem0 available → memory enabled

## Changing the Option

### Enabling Memory

When you enable memory:

1. **Immediate Effect**: Next conversation uses memory
2. **Agent Recreation**: New agents created with mem0 tool
3. **Memory Storage**: Starts storing memories
4. **AWS Costs**: Bedrock calls for embeddings/LLM begin

**Example**:
```yaml
# Before: Memory disabled
User: "I like coffee"
Agent: "Noted"  # Not stored

# Enable memory in config

# After: Memory enabled
User: "I like coffee"
Agent: [Stores in mem0] "I'll remember that"

User: "What do I like?"
Agent: "You like coffee"  # Retrieved from memory
```

### Disabling Memory

When you disable memory:

1. **Immediate Effect**: Next conversation has no memory
2. **Agent Recreation**: New agents created without mem0 tool
3. **Existing Memories**: Preserved in mem0 (not deleted)
4. **AWS Costs**: No more Bedrock calls for memory

**Example**:
```yaml
# Before: Memory enabled
User: "I like coffee"
Agent: [Stored in mem0]

# Disable memory in config

# After: Memory disabled
User: "What do I like?"
Agent: "I don't have that information"  # Can't access memory

# Note: Memory still exists in mem0, just not accessible
```

### Re-enabling Memory

When you re-enable memory:

1. **Previous Memories**: Still available in mem0
2. **Immediate Access**: Agent can retrieve old memories
3. **Continuity**: Picks up where it left off

**Example**:
```yaml
# Memory enabled → disabled → enabled again
User: "I like coffee"  # Stored when enabled
# Disable memory
# Re-enable memory
User: "What do I like?"
Agent: "You like coffee"  # Old memory still accessible
```

## Memory Stats Service

Check memory status with the service:

```yaml
service: bedrock_agent.get_memory_stats
```

**When memory enabled**:
```json
{
  "memory_enabled": true,
  "mem0_available": true,
  "user_id": "entry_id",
  "cached_conversations": 2,
  "tools_count": 1
}
```

**When memory disabled**:
```json
{
  "memory_enabled": false,
  "mem0_available": true,
  "user_id": "entry_id",
  "cached_conversations": 0,
  "tools_count": 0
}
```

## Cost Implications

### Memory Enabled

**AWS Bedrock Costs**:
- Embeddings: ~$0.0001 per memory (Titan v2)
- LLM Processing: ~$0.001 per memory (Claude 3.5 Haiku)
- Total: ~$0.0011 per memory operation

**Typical Usage**:
- 10 memories/day: ~$0.33/month
- 50 memories/day: ~$1.65/month
- 100 memories/day: ~$3.30/month

### Memory Disabled

**AWS Bedrock Costs**:
- No memory-related costs
- Only conversation costs (same as before)

## Privacy Considerations

### Memory Enabled

- Conversations are stored in mem0
- Memories persist across sessions
- User-specific memory isolation
- Stored locally by default (FAISS)

**Privacy Features**:
- Per-user memory isolation
- No cross-user access
- Local storage (no cloud by default)
- Can be cleared via mem0 API

### Memory Disabled

- No conversation storage
- Each conversation is independent
- No persistent data
- Maximum privacy

## Troubleshooting

### Memory Option Not Visible

**Cause**: Old config entry without option

**Solution**:
1. Go to integration settings
2. Click "Configure"
3. Option should appear (defaults to enabled)
4. Save to persist setting

### Memory Not Working Despite Being Enabled

**Check**:
1. Run `bedrock_agent.get_memory_stats`
2. Look for `mem0_available: false`
3. Check logs for warnings

**Common Issues**:
- `strands-agents-tools[mem0_memory]` not installed
- `faiss-cpu` not installed
- AWS credentials not configured

**Solution**:
```bash
pip install 'strands-agents-tools[mem0_memory]'
pip install faiss-cpu
```

### Memory Enabled But No Memories Stored

**Check**:
1. Verify option is enabled in config
2. Check logs for memory operations
3. Test with explicit memory command

**Test**:
```
User: "Remember that I like coffee"
Agent: Should store in memory
```

If not working, check logs for errors.

### Want to Clear Memories

**Option 1**: Disable and re-enable memory
- Memories persist but agent won't use them
- Re-enabling gives access again

**Option 2**: Clear mem0 storage
```bash
# Delete FAISS storage
rm -rf /tmp/mem0_384_faiss
```

**Option 3**: Use mem0 API
```python
from mem0 import Memory
memory = Memory()
memory.delete_all(user_id="your_user_id")
```

## Best Practices

### 1. Start with Memory Enabled

- Try memory features first
- Evaluate usefulness
- Disable if not needed

### 2. Consider Privacy

- Inform users about memory
- Provide way to disable
- Respect user preferences

### 3. Monitor Costs

- Check AWS Bedrock usage
- Set budget alerts
- Disable if costs too high

### 4. Test Both Modes

- Test with memory enabled
- Test with memory disabled
- Verify behavior matches expectations

### 5. Document for Users

- Explain what memory does
- Show how to enable/disable
- Provide examples

## Migration

### From Previous Versions

If upgrading from version without memory option:

1. **Default Behavior**: Memory enabled by default
2. **No Action Needed**: Works automatically
3. **Can Disable**: Use options flow to disable
4. **No Breaking Changes**: Existing setup continues working

### To Future Versions

The option is stored in config entry options:
- Persists across updates
- No migration needed
- Setting preserved

## Summary

✅ **Configuration Option**: Enable/disable memory in UI
✅ **Default**: Memory enabled by default
✅ **Changeable**: Can toggle anytime in options flow
✅ **Immediate Effect**: Changes apply to next conversation
✅ **Graceful**: Works with or without mem0 installed
✅ **User Control**: Users decide if they want memory

The memory configuration option gives users full control over long-term memory functionality!
