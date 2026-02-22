# Advanced Memory Options for Bedrock Agent

## Overview

There are three memory solutions available for your Strands Agent, each with different capabilities and use cases:

1. **FileSessionManager** (Current Implementation) - Basic conversation persistence
2. **Mem0.ai** - Advanced semantic memory with intelligent retrieval
3. **Amazon AgentCore Memory** - Enterprise-grade memory with multiple strategies

## Comparison

| Feature | FileSessionManager | Mem0.ai | AgentCore Memory |
|---------|-------------------|---------|------------------|
| **Setup Complexity** | ✅ Simple | ⚠️ Moderate | ⚠️ Moderate |
| **Installation** | Built-in | `pip install mem0ai` | `pip install bedrock-agentcore[strands-agents]` |
| **Storage** | Local files | Local/Cloud | AWS Bedrock |
| **Semantic Search** | ❌ No | ✅ Yes | ✅ Yes |
| **Long-term Memory** | ⚠️ Limited | ✅ Yes | ✅ Yes |
| **User Preferences** | ❌ No | ✅ Yes | ✅ Yes (strategy) |
| **Session Summaries** | ❌ No | ⚠️ Manual | ✅ Yes (strategy) |
| **Fact Extraction** | ❌ No | ✅ Yes | ✅ Yes (strategy) |
| **Multi-user** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Cost** | Free | Free/Paid | AWS charges |
| **Best For** | Simple chatbots | Personalized agents | Enterprise apps |

## Option 1: FileSessionManager (Current)

### What You Have Now

```python
session_manager = FileSessionManager(
    session_id=conversation_id,
    storage_dir="/tmp/strands"
)
```

### Pros
- ✅ Already implemented
- ✅ No additional dependencies
- ✅ Simple and reliable
- ✅ Works offline

### Cons
- ❌ No semantic search
- ❌ No intelligent memory retrieval
- ❌ Limited to conversation history
- ❌ No automatic fact extraction

### Use Case
Perfect for basic conversation continuity where you just need the agent to remember what was said in the current conversation.

## Option 2: Mem0.ai (Recommended for Personalization)

### Overview

Mem0.ai provides intelligent, semantic memory that can:
- Store and retrieve memories based on meaning, not just keywords
- Extract and remember user preferences automatically
- Provide relevant context across multiple conversations
- Work as a tool that the agent can call

### Installation

```bash
pip install mem0ai
```

### Implementation

```python
from strands_agents_tools.community.mem0 import mem0_memory
from strands import Agent

# Create agent with mem0 memory tool
agent = Agent(
    system_prompt="You are a helpful assistant with memory capabilities.",
    tools=[mem0_memory],
)

# The agent can now:
# 1. Store memories: "Remember that I prefer vegetarian food"
# 2. Retrieve memories: "What do you know about my food preferences?"
# 3. List memories: "Show me all my memories"
```

### Key Features

**1. Semantic Memory Storage**
```python
# User says: "I love Italian food"
# Mem0 stores: User preference for Italian cuisine

# Later, user asks: "What should I eat for dinner?"
# Mem0 retrieves: Italian food preference
# Agent responds: "Based on your love for Italian food, how about pasta?"
```

**2. Automatic Fact Extraction**
- Automatically identifies and stores important information
- No need to explicitly say "remember this"
- Intelligent relevance scoring

**3. Cross-Conversation Memory**
- Memories persist across different conversation sessions
- User preferences available in all conversations
- Long-term relationship building

### Integration with Home Assistant

```python
class StrandsAgentWrapper:
    def __init__(self, ...):
        from strands_agents_tools.community.mem0 import mem0_memory
        
        # Add mem0 as a tool
        self.tools = [mem0_memory]
        
        # Agent can now use memory automatically
        self.agent = Agent(
            model=bedrock_model,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )
```

### Pros
- ✅ Semantic search and retrieval
- ✅ Automatic preference learning
- ✅ Works as a tool (agent decides when to use it)
- ✅ Cross-conversation memory
- ✅ Easy to integrate
- ✅ Free tier available

### Cons
- ⚠️ Requires external service (can be self-hosted)
- ⚠️ Additional dependency
- ⚠️ May need API key for cloud version

### Use Case
Ideal for personalized assistants that need to remember user preferences, habits, and facts across multiple conversations.

## Option 3: Amazon AgentCore Memory (Recommended for Enterprise)

### Overview

Amazon Bedrock AgentCore Memory provides enterprise-grade memory with three built-in strategies:

1. **Summary Memory Strategy** - Automatically summarizes conversations
2. **User Preference Memory Strategy** - Learns and stores preferences
3. **Semantic Memory Strategy** - Extracts and stores facts

### Installation

```bash
pip install 'bedrock-agentcore[strands-agents]'
```

### Implementation

#### Step 1: Create Memory Resource (One-time Setup)

```python
from bedrock_agentcore.memory import MemoryClient

client = MemoryClient(region_name="us-east-1")
memory = client.create_memory_and_wait(
    name="HomeAssistantMemory",
    description="Memory for Home Assistant Bedrock Agent",
    strategies=[
        {
            "summaryMemoryStrategy": {
                "name": "SessionSummarizer",
                "namespaces": ["/summaries/{actorId}/{sessionId}"]
            }
        },
        {
            "userPreferenceMemoryStrategy": {
                "name": "PreferenceLearner",
                "namespaces": ["/preferences/{actorId}"]
            }
        },
        {
            "semanticMemoryStrategy": {
                "name": "FactExtractor",
                "namespaces": ["/facts/{actorId}"]
            }
        }
    ]
)

memory_id = memory.get('id')
print(f"Memory ID: {memory_id}")  # Save this for your config
```

#### Step 2: Use in Strands Wrapper

```python
from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager
)

class StrandsAgentWrapper:
    def get_agent_with_agentcore_memory(self, conversation_id: str, user_id: str) -> Agent:
        """Get agent with AgentCore Memory."""
        
        config = AgentCoreMemoryConfig(
            memory_id=self.agentcore_memory_id,  # From config
            session_id=conversation_id,
            actor_id=user_id,
            retrieval_config={
                "/preferences/{actorId}": RetrievalConfig(
                    top_k=5,
                    relevance_score=0.7
                ),
                "/facts/{actorId}": RetrievalConfig(
                    top_k=10,
                    relevance_score=0.3
                ),
                "/summaries/{actorId}/{sessionId}": RetrievalConfig(
                    top_k=5,
                    relevance_score=0.5
                )
            }
        )
        
        with AgentCoreMemorySessionManager(
            agentcore_memory_config=config,
            region_name=self.region_name
        ) as session_manager:
            return Agent(
                model=self.bedrock_model,
                session_manager=session_manager,
                system_prompt=self.system_prompt,
            )
```

### Key Features

**1. Multiple Memory Strategies**
- **Summaries**: Automatic conversation summarization
- **Preferences**: Learns what users like/dislike
- **Facts**: Extracts and stores factual information

**2. Intelligent Retrieval**
- Semantic search across all memory types
- Configurable relevance thresholds
- Top-K retrieval per namespace

**3. Namespace Organization**
```
/preferences/{actorId}        # User preferences across all sessions
/facts/{actorId}              # User facts across all sessions
/summaries/{actorId}/{sessionId}  # Session-specific summaries
```

**4. Message Batching**
- Reduce API calls with batching
- Configurable batch size
- Automatic flushing

### Pros
- ✅ Enterprise-grade reliability
- ✅ Multiple memory strategies
- ✅ Automatic summarization
- ✅ Intelligent retrieval
- ✅ AWS integration
- ✅ Scalable

### Cons
- ⚠️ AWS charges apply
- ⚠️ More complex setup
- ⚠️ Requires AWS Bedrock access
- ⚠️ One agent per session limitation

### Use Case
Best for production Home Assistant deployments where you need enterprise-grade memory with automatic summarization and preference learning.

## Recommendation

### For Your Use Case

Given that you're already using AWS Bedrock, I recommend **Amazon AgentCore Memory** for the following reasons:

1. **Native Integration** - Already using Bedrock, so no new services
2. **Automatic Strategies** - Summaries, preferences, and facts automatically extracted
3. **Enterprise Grade** - Reliable, scalable, and supported by AWS
4. **Intelligent Retrieval** - Semantic search with configurable relevance
5. **Multi-user Support** - Perfect for Home Assistant with multiple users

### Implementation Plan

**Phase 1: Add AgentCore Memory Support**
1. Add configuration option for memory type
2. Implement AgentCore Memory session manager
3. Add memory ID to config entry options
4. Test with single user

**Phase 2: Enhance with User Context**
1. Map Home Assistant user IDs to actor IDs
2. Implement per-user memory isolation
3. Add memory management services
4. Test with multiple users

**Phase 3: Optimize**
1. Configure retrieval thresholds
2. Implement message batching
3. Add memory analytics
4. Monitor AWS costs

### Quick Start

Want to try it now? Here's the minimal change:

```python
# In strands_wrapper.py
def __init__(self, ..., memory_type="file", agentcore_memory_id=None):
    self.memory_type = memory_type
    self.agentcore_memory_id = agentcore_memory_id
    
    if memory_type == "agentcore" and agentcore_memory_id:
        # Use AgentCore Memory
        self._use_agentcore_memory = True
    else:
        # Use FileSessionManager (current)
        self._use_agentcore_memory = False
```

## Alternative: Hybrid Approach

You could also use **both**:

1. **FileSessionManager** - For basic conversation history (free, simple)
2. **Mem0 as a Tool** - For explicit memory operations (user says "remember this")

This gives you:
- ✅ Free conversation continuity
- ✅ Explicit memory when needed
- ✅ No AWS charges for memory
- ✅ Simple implementation

```python
from strands_agents_tools.community.mem0 import mem0_memory

agent = Agent(
    model=bedrock_model,
    session_manager=FileSessionManager(...),  # Basic history
    tools=[mem0_memory],  # Explicit memory
    system_prompt=self.system_prompt,
)
```

## Next Steps

1. **Review** the options and decide which fits your needs
2. **Test** with a small implementation
3. **Measure** memory usage and costs
4. **Scale** to production

Would you like me to implement any of these options?
