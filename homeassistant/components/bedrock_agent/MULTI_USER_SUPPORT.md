# Multi-User Memory Support

## Overview

The Bedrock Agent integration now supports true multi-user memory isolation using Home Assistant's user context. Each user gets their own personal memory space, ensuring privacy and personalized experiences.

## How It Works

### User ID from Context

The integration uses `context.user_id` from Home Assistant's conversation context:

```python
# In agent.py
user_input.context.user_id  # Home Assistant user ID
    ↓
# Passed to strands_wrapper
generate_response(..., context_user_id=user_input.context.user_id)
    ↓
# Used for memory isolation
mem0_memory(action="store", user_id=context_user_id, ...)
```

### Memory Isolation

Each user's memories are completely isolated:

```
User A (user_id: "abc123")
├── Memory: "I prefer dark mode"
├── Memory: "My favorite color is blue"
└── Memory: "I have a dog named Max"

User B (user_id: "def456")
├── Memory: "I prefer light mode"
├── Memory: "My favorite color is red"
└── Memory: "I have a cat named Luna"
```

User A cannot access User B's memories and vice versa.

### Agent Caching

Agents are cached per conversation AND user:

```python
cache_key = f"{conversation_id}_{user_id}"
```

This ensures:
- Each user gets their own agent instance
- Memories are retrieved for the correct user
- No memory leakage between users

## User Scenarios

### Scenario 1: Multiple Users, Same Device

**Setup**: Family tablet with multiple Home Assistant users

```
Dad (user_id: "dad_123"):
  "Remember I like coffee at 7am"
  
Mom (user_id: "mom_456"):
  "Remember I like tea at 8am"
  
# Later...
Dad: "What time do I like my morning drink?"
Agent: "You like coffee at 7am"

Mom: "What time do I like my morning drink?"
Agent: "You like tea at 8am"
```

Each user gets their own personalized response!

### Scenario 2: Guest User

**Setup**: Guest using Home Assistant

```
Guest (user_id: None or "guest"):
  "Remember I'm visiting for the weekend"
  
# Falls back to config entry ID
# Memories stored under entry_id instead of user_id
```

### Scenario 3: Automation (No User Context)

**Setup**: Automation triggering conversation

```
Automation (user_id: None):
  "What's the weather?"
  
# Falls back to config entry ID
# No personal memories, just general responses
```

## Implementation Details

### User ID Priority

1. **Context User ID** (preferred): `context.user_id` from conversation
2. **Fallback**: Config entry ID if no user context

```python
effective_user_id = context_user_id or self.user_id
```

### System Prompt Enhancement

The agent's system prompt includes the user_id:

```python
memory_instructions = f"""
IMPORTANT: When using the memory tool, always use user_id="{effective_user_id}" 
to ensure memories are stored and retrieved for the correct user.
"""
```

This ensures the LLM always uses the correct user_id when calling mem0_memory.

### Cache Management

Cache keys combine conversation and user:

```python
cache_key = f"{conversation_id}_{user_id}"
self._agent_cache[cache_key] = agent
```

Benefits:
- Same conversation, different users → different agents
- Different conversations, same user → different agents
- Efficient memory usage with proper isolation

## Privacy & Security

### Memory Isolation

✅ **Complete Isolation**: Each user's memories are separate
✅ **No Cross-Access**: User A cannot see User B's memories
✅ **Secure Storage**: Memories stored with user_id in mem0
✅ **Context-Based**: Uses Home Assistant's authentication

### User Authentication

The integration relies on Home Assistant's authentication:
- Users must be logged in to Home Assistant
- User ID comes from authenticated session
- No additional authentication needed

### Data Privacy

- Memories stored locally by default (FAISS)
- User ID used as namespace in mem0
- No memory sharing between users
- Each user's data is isolated

## Testing Multi-User Support

### Test 1: Different Users, Different Memories

```yaml
# As User A
User A: "Remember I prefer 72°F"
Agent: "I'll remember you prefer 72°F"

# As User B
User B: "Remember I prefer 68°F"
Agent: "I'll remember you prefer 68°F"

# Verify isolation
User A: "What temperature do I prefer?"
Agent: "You prefer 72°F"  # ✅ Correct

User B: "What temperature do I prefer?"
Agent: "You prefer 68°F"  # ✅ Correct
```

### Test 2: Same Conversation, Different Users

```yaml
# User A starts conversation
User A: "Remember my favorite color is blue"

# User B joins same conversation (different device)
User B: "What's my favorite color?"
Agent: "I don't have that information"  # ✅ Correct - different user

User B: "Remember my favorite color is red"

# Verify
User A: "What's my favorite color?"
Agent: "Your favorite color is blue"  # ✅ Correct

User B: "What's my favorite color?"
Agent: "Your favorite color is red"  # ✅ Correct
```

### Test 3: Guest User (No Context)

```yaml
# Guest user (no authentication)
Guest: "Remember I'm visiting"
Agent: [Stores under entry_id]

# Later, as authenticated user
User A: "Who's visiting?"
Agent: "I don't have that information"  # ✅ Correct - different user_id
```

## Logging

### Debug Logs

Enable debug logging to see user ID usage:

```yaml
logger:
  default: info
  logs:
    homeassistant.components.bedrock_agent: debug
```

Look for:
```
DEBUG: Creating new agent with mem0 memory for user: abc123, conversation: xyz789
DEBUG: Using cached agent for conversation: xyz789, user: abc123
```

### User ID in Logs

User IDs are logged for troubleshooting:
- Agent creation: Shows user_id
- Cache hits: Shows user_id
- Memory operations: Shows user_id (in mem0 tool)

## Services

### Get Memory Stats

Check memory stats including user info:

```yaml
service: bedrock_agent.get_memory_stats
```

Returns:
```json
{
  "memory_enabled": true,
  "mem0_available": true,
  "user_id": "entry_id_fallback",
  "cached_conversations": 3,
  "tools_count": 1
}
```

**Note**: Shows fallback user_id, not context user_id (which varies per request)

### Clear Cache

Clear cache for specific conversation:

```yaml
service: bedrock_agent.clear_conversation_cache
data:
  conversation_id: "xyz789"
```

This clears cache for ALL users in that conversation.

## Best Practices

### 1. User Authentication

Ensure users are authenticated:
- Use Home Assistant's built-in authentication
- Don't share accounts between users
- Each person should have their own user account

### 2. Privacy

Inform users about memory:
- Explain that conversations are remembered
- Provide way to clear personal memories
- Respect user privacy preferences

### 3. Testing

Test with multiple users:
- Create test users in Home Assistant
- Verify memory isolation
- Check cache behavior

### 4. Fallback Handling

Handle cases without user context:
- Automations may not have user_id
- Guest access may not have user_id
- Fallback to entry_id is acceptable

## Troubleshooting

### Issue: Memories Shared Between Users

**Symptom**: User A sees User B's memories

**Cause**: User context not being passed correctly

**Solution**:
1. Check logs for user_id in agent creation
2. Verify Home Assistant authentication
3. Ensure users are logged in
4. Check if fallback is being used

### Issue: No User Context

**Symptom**: All memories stored under entry_id

**Cause**: Conversation not initiated by authenticated user

**Solution**:
1. Ensure user is logged in to Home Assistant
2. Check if automation is triggering (no user context)
3. Verify conversation source has user context

### Issue: Cache Not Working

**Symptom**: Agent created on every request

**Cause**: Cache key mismatch

**Solution**:
1. Check logs for cache key format
2. Verify conversation_id is consistent
3. Ensure user_id is consistent

## Advanced Configuration

### Custom User ID Mapping

If you need custom user ID mapping, you can override in code:

```python
# In agent.py
custom_user_id = map_user_id(user_input.context.user_id)
return await self.strands_agent_wrapper.generate_response(
    initial_question,
    user_input.as_llm_context(self.entry.domain),
    user_input.conversation_id,
    custom_user_id,  # Use custom mapping
)
```

### Shared Memories

If you want some memories shared across users:

```python
# Store with special shared user_id
mem0_memory(action="store", user_id="shared", content="...")

# Retrieve from shared space
mem0_memory(action="retrieve", user_id="shared", query="...")
```

**Note**: This requires custom implementation.

## Migration from Single User

### Before (Entry ID Only)

```python
user_id = entry.entry_id  # Same for all users
```

All users shared the same memory space.

### After (Context User ID)

```python
user_id = context.user_id or entry.entry_id  # Per-user
```

Each user has their own memory space.

### Migration Steps

1. **No action needed**: Existing memories stay under entry_id
2. **New memories**: Stored per-user automatically
3. **Old memories**: Accessible when user_id falls back to entry_id
4. **Clean migration**: No data loss or conflicts

## Future Enhancements

Potential improvements:
1. **Memory Sharing**: Allow users to share specific memories
2. **Family Memories**: Shared memory space for family members
3. **Memory Export**: Export user's memories for backup
4. **Memory Import**: Import memories for new users
5. **Admin Tools**: View/manage memories across users

## Resources

- **Home Assistant Users**: https://www.home-assistant.io/docs/authentication/
- **Context Object**: https://developers.home-assistant.io/docs/dev_101_hass/#context
- **Mem0 Documentation**: https://docs.mem0.ai
- **Multi-User Best Practices**: https://www.home-assistant.io/docs/configuration/securing/
