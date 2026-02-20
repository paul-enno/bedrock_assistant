# 🚀 Amazon Bedrock Agent v2.0.0-beta - Major Refactoring Release

We're excited to announce a major architectural upgrade to the Amazon Bedrock Agent integration! This beta release represents a complete refactoring with powerful new capabilities for memory, multi-user support, and enhanced conversation experiences.

## ⚠️ Beta Release Notice

This is a **beta release** for testing and feedback. While we've thoroughly tested the changes, please report any issues you encounter. The integration maintains backward compatibility with existing configurations.

## 🎯 What's New

### 🔄 Migration to Strands SDK

We've completely rebuilt the integration on top of the [Strands Agents SDK](https://github.com/strands-agents/sdk-python), providing a more robust and extensible foundation:

- **Better Architecture**: Leverages Strands' proven agent framework
- **Improved Reliability**: Built-in retry logic and error handling
- **Future-Ready**: Easier to add new features and capabilities
- **Tool Integration**: Native support for tool calling and function execution

### 🧠 Three-Tier Memory System

The integration now features a sophisticated memory architecture that transforms how the agent remembers and learns:

#### 1️⃣ Short-Term Memory (Conversation Manager)
- Maintains last 40 messages in active context
- Optimized for LLM token limits
- Automatic context window management

#### 2️⃣ Persistent Storage (Session Manager)
- **Full conversation history** saved to disk
- Survives Home Assistant restarts
- Complete audit trail of all interactions
- User-isolated storage

#### 3️⃣ Long-Term Semantic Memory (Mem0)
- **Learns and remembers** important information across all conversations
- Semantic search powered by FAISS vector database
- Personalized responses based on learned preferences
- **Configurable memory guidelines** - Control what gets stored in any language
- Examples:
  - "Remember that I prefer metric units"
  - "My dog's name is Max" (recalled in future conversations)
  - "I usually wake up at 7 AM" (used for context-aware responses)

**Configuration**: 
- Memory can be enabled/disabled in integration options
- Custom storage paths supported
- **NEW**: Editable memory guidelines to control storage behavior
- Multi-language support for memory instructions

### 👥 Multi-User Session Management

Complete user isolation and personalization:

- **Per-User Sessions**: Each Home Assistant user gets their own isolated agent
- **Private Conversations**: Your conversations stay private from other users
- **Personalized Memory**: Each user's preferences and learned information is separate
- **Family-Friendly**: Perfect for households with multiple users
- **Persistent State**: All user data survives restarts

### 🏠 Enhanced Home Assistant Control

Natural language control of your smart home (when enabled):

```
"Turn on the kitchen lights"
"Set bedroom lights to 50% brightness"
"What's the temperature in the living room?"
"Add milk to my shopping list"
"Activate movie night scene"
```

Supports lights, switches, covers, climate, media players, locks, fans, scenes, scripts, and more!

### 📚 Comprehensive Documentation

New detailed README covering:
- Feature explanations
- Configuration guide
- Usage examples
- Troubleshooting tips
- Architecture details

## 🔧 Breaking Changes

### Removed Features (Temporarily)

To focus on the core conversation experience and new memory capabilities, we've temporarily removed:

- ❌ **Bedrock Agents**: Native AWS Bedrock Agent support
- ❌ **Knowledge Bases**: AWS Bedrock Knowledge Base integration

These features will return in future releases with improved integration into the new architecture.

### What Still Works

✅ All foundation model support (Claude, Titan, Llama, etc.)
✅ Conversation agent functionality
✅ Cognitive task service (image analysis)
✅ AWS credential configuration
✅ Custom system prompts
✅ Existing configurations (no migration needed)

## 📦 Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "Amazon Bedrock Agent"
3. Install and restart Home Assistant
4. Configure through UI (Settings → Devices & Services)

### Manual Installation

1. Copy `custom_components/bedrock_agent` to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Configure through UI

## ⚙️ Configuration

### Required Settings
- AWS Access Key ID
- AWS Secret Access Key
- AWS Region
- Model Selection

### Optional Settings
- **Enable Home Assistant Control**: Allow device control through conversation
- **Enable Long-term Memory**: Enable Mem0 semantic memory (requires `faiss-cpu`)
- **Memory Storage Path**: Custom path for memory data
- **Memory Storage Guidelines**: Customize what information gets stored (supports any language)
- **Prompt Context**: Custom system prompt

## 🧪 Testing This Beta

We'd love your feedback on:

1. **Memory System**: Does the agent remember information correctly?
2. **Multi-User**: Do different users have isolated experiences?
3. **Home Assistant Control**: Does device control work as expected?
4. **Performance**: Any issues with response times or resource usage?
5. **Stability**: Any crashes or errors?

Please report issues on [GitHub Issues](https://github.com/your-repo/issues) with:
- Home Assistant version
- Integration version
- Detailed description of the issue
- Relevant logs (enable debug logging)

## 🗺️ Roadmap

We're actively working on exciting new features:

### Coming Soon

🔌 **MCP (Model Context Protocol) Integration**
- Connect external tools and services
- Extensible tool ecosystem
- Community-contributed integrations

📚 **Knowledge Bases**
- Return of AWS Bedrock Knowledge Base support
- Enhanced with new memory system
- Better context retrieval

🛡️ **Guardrails**
- Content filtering and safety
- PII detection and redaction
- Custom policy enforcement

🏠 **Local Model Hosting**
- Run models locally on your hardware
- Privacy-focused option
- Reduced cloud costs
- Support for Ollama and other local LLM servers

### Future Enhancements
- Advanced conversation patterns
- Multi-agent orchestration
- Custom memory strategies
- Enhanced personalization
- Integration with more Home Assistant features

## 📊 Technical Details

### New Dependencies
- `strands-agents==1.26.0` - Agent framework
- `strands-agents-tools[mem0_memory]==0.1.19` - Memory tools
- `faiss-cpu==1.9.0` - Vector database (optional, for memory)

### Storage Requirements
- Session storage: ~1-10 MB per active user
- Memory storage: ~10-100 MB per user (if enabled)
- Scales with conversation volume

### Performance
- Efficient caching strategies
- Lazy loading of resources
- Optimized session storage
- Minimal memory footprint
- **All blocking I/O operations run in executor threads**
- No event loop blocking warnings

## 🐛 Known Issues

- None currently identified in beta testing

## ✨ Latest Updates (v2.0.0-beta.2)

### New Features
- **Configurable Memory Guidelines**: Customize what the agent stores in memory through the UI
- **Multi-Language Support**: Memory guidelines can be written in any language
- **Selective Memory Storage**: Default guidelines prevent storing greetings and casual conversation

### Performance Improvements
- All blocking I/O operations now run in executor threads
- BedrockModel creation optimized (no event loop blocking)
- FileSessionManager creation optimized (no event loop blocking)
- Agent initialization optimized (no event loop blocking)

### Bug Fixes
- Fixed Bedrock ValidationException handling with automatic retry
- Corrupted session files now automatically cleared and retried
- Fixed all code quality issues (ruff, mypy, pylint compliant)
- Fixed variable shadowing in HA control tool
- Improved error logging patterns

## 🙏 Acknowledgments

This release builds on:
- [Strands Agents SDK](https://github.com/strands-agents/sdk-python) by AWS
- [Mem0](https://github.com/mem0ai/mem0) for semantic memory
- [FAISS](https://github.com/facebookresearch/faiss) by Meta for vector search
- Home Assistant conversation and intent systems

## 📝 Changelog

### Added
- Strands SDK integration for robust agent framework
- Three-tier memory system (short-term, persistent, semantic)
- Multi-user session management with complete isolation
- Enhanced Home Assistant device control
- Comprehensive README documentation
- Memory management services
- User-specific memory storage
- **Configurable memory guidelines in UI**
- **Multi-language support for memory instructions**
- **Automatic retry mechanism for Bedrock validation errors**

### Changed
- Complete architectural refactoring
- Improved error handling and logging
- Better async/await patterns
- Enhanced configuration flow
- Optimized performance and caching
- **All blocking I/O moved to executor threads**

### Removed
- Bedrock Agent support (temporary)
- Knowledge Base integration (temporary)

### Fixed
- Various stability improvements
- Better error messages
- Improved type safety
- **Event loop blocking warnings eliminated**
- **Corrupted session file handling**
- **Code quality issues (ruff, mypy, pylint)**

## 🔗 Links

- [Documentation](https://github.com/your-repo/blob/main/README.md)
- [Issue Tracker](https://github.com/your-repo/issues)
- [Discussions](https://github.com/your-repo/discussions)

---

**Thank you for testing this beta release!** Your feedback helps make this integration better for everyone. 🎉
