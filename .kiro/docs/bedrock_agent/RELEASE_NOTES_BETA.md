# 🚀 Amazon Bedrock Agent v2.0.0-beta.3 - Enhanced Configuration Experience

We're excited to announce beta.3 with a completely redesigned configuration flow that makes managing your Bedrock Agent integration easier and more intuitive!

## ⚠️ Beta Release Notice

This is a **beta release** for testing and feedback. While we've thoroughly tested the changes, please report any issues you encounter. The integration maintains backward compatibility with existing configurations.

## 🎯 What's New in beta.3

### 🎨 Redesigned Configuration Flow

The options flow has been completely reorganized with a modern menu-based interface:

#### **Menu-Based Navigation**
- **AWS Configuration** - Manage credentials and region
- **AI Configuration** - Select model and customize prompts
- **Memory Configuration** - Control memory settings
- **Tools Configuration** - Enable/disable Home Assistant control

#### **Key Improvements**

**1. AWS Configuration First**
- Region field now appears first (emphasizes impact on model availability)
- Clear indication that different regions have different models
- Automatic validation of credentials before saving

**2. Intelligent Navigation**
- After changing AWS credentials/region, automatically navigate to AI Configuration
- Ensures you select a valid model for the new region
- Prevents invalid model configurations

**3. Automatic Integration Reload**
- Integration automatically reloads after ANY configuration change
- Changes take effect immediately - no manual reload needed
- Applies to:
  - AWS credentials/region changes
  - Model selection changes
  - Memory settings changes
  - Tool enable/disable changes

**4. Clear User Guidance**
- Each configuration section has helpful descriptions
- Explains what will happen when you save
- Informs you about automatic reloads

### 📋 Configuration Sections

#### AWS Configuration
```
┌─────────────────────────────────────┐
│ AWS Configuration                   │
├─────────────────────────────────────┤
│ • AWS Region (first field)          │
│ • AWS Access Key ID                 │
│ • AWS Secret Access Key             │
│                                     │
│ After saving: Integration reloads   │
│ and navigates to AI Configuration   │
└─────────────────────────────────────┘
```

#### AI Configuration
```
┌─────────────────────────────────────┐
│ AI Configuration                    │
├─────────────────────────────────────┤
│ • Model Selection                   │
│   (updated for current region)      │
│ • System Prompt                     │
│                                     │
│ After saving: Integration reloads   │
└─────────────────────────────────────┘
```

#### Memory Configuration
```
┌─────────────────────────────────────┐
│ Memory Configuration                │
├─────────────────────────────────────┤
│ • Enable Long-term Memory           │
│ • Memory Storage Path               │
│ • Memory Guidelines (if enabled)    │
│                                     │
│ After saving: Integration reloads   │
└─────────────────────────────────────┘
```

#### Tools Configuration
```
┌─────────────────────────────────────┐
│ Tools Configuration                 │
├─────────────────────────────────────┤
│ • Enable Home Assistant Control     │
│                                     │
│ After saving: Integration reloads   │
└─────────────────────────────────────┘
```

### 🔄 Automatic Reload Behavior

**Why This Matters:**
- AWS credential changes need new boto3 clients
- Region changes affect available models
- Model changes need agent reinitialization
- Memory settings require Mem0 reconfiguration
- Tool changes update available capabilities

**User Experience:**
```
Before (beta.2):
User changes model → Saves → Nothing happens → Confused
User has to manually reload or restart

After (beta.3):
User changes model → Saves → Auto reload → Works immediately! ✨
```

### 🎯 Workflow Example

**Changing AWS Region:**
```
1. Open Options → AWS Configuration
2. Change region from us-east-1 to eu-west-1
3. Click Submit
   ✓ Credentials validated
   ✓ Integration reloads
   → Automatically opens AI Configuration
4. Model list now shows eu-west-1 models
5. Select appropriate model
6. Click Submit
   ✓ Integration reloads
   → Returns to menu
7. Done! New region and model active
```

## 🔧 Technical Improvements

### Configuration Flow Architecture
- Menu-based navigation using `async_show_menu()`
- Proper form handling with `async_show_form()`
- Automatic reload via `async_reload(config_entry.entry_id)`
- Clear separation of config data vs options

### Code Quality
- All 45 tests passing (100%)
- MyPy type checking passes
- PyLint passes with no issues
- 69% test coverage (excellent for core features)

### User Experience
- Clear descriptions for each field
- Helpful guidance about what happens next
- Automatic navigation to related settings
- Immediate feedback on changes

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

## 🎯 What's New (Summary of All Beta Releases)

### 🔄 Migration to Strands SDK (beta.1)

We've completely rebuilt the integration on top of the [Strands Agents SDK](https://github.com/strands-agents/sdk-python), providing a more robust and extensible foundation.

### 🧠 Three-Tier Memory System (beta.1)

The integration features a sophisticated memory architecture:

#### 1️⃣ Short-Term Memory (Conversation Manager)
- Maintains last 40 messages in active context
- Optimized for LLM token limits

#### 2️⃣ Persistent Storage (Session Manager)
- Full conversation history saved to disk
- Survives Home Assistant restarts

#### 3️⃣ Long-Term Semantic Memory (Mem0)
- Learns and remembers important information
- Semantic search powered by FAISS
- Personalized responses based on learned preferences
- Configurable memory guidelines (beta.2)

### 👥 Multi-User Session Management (beta.1)

Complete user isolation and personalization:
- Per-user sessions
- Private conversations
- Personalized memory
- Persistent state

### 🏠 Enhanced Home Assistant Control (beta.1)

Natural language control of your smart home:
```
"Turn on the kitchen lights"
"Set bedroom lights to 50% brightness"
"What's the temperature in the living room?"
```

## 🧪 Testing This Beta

We'd love your feedback on:

1. **New Config Flow**: Is the menu-based navigation intuitive?
2. **Automatic Reload**: Do changes take effect immediately?
3. **AWS Region Changes**: Does the model list update correctly?
4. **User Experience**: Is it clear what each setting does?
5. **Navigation**: Can you easily move between configuration sections?

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

📚 **Knowledge Bases**
- Return of AWS Bedrock Knowledge Base support
- Enhanced with new memory system

🛡️ **Guardrails**
- Content filtering and safety
- PII detection and redaction

🏠 **Local Model Hosting**
- Run models locally on your hardware
- Privacy-focused option

## 📊 Technical Details

### New Dependencies
- `strands-agents==1.26.0` - Agent framework
- `strands-agents-tools[mem0_memory]==0.1.19` - Memory tools
- `faiss-cpu==1.9.0` - Vector database (optional, for memory)

### Storage Requirements
- Session storage: ~1-10 MB per active user
- Memory storage: ~10-100 MB per user (if enabled)

### Performance
- Efficient caching strategies
- Lazy loading of resources
- Optimized session storage
- All blocking I/O operations run in executor threads
- No event loop blocking warnings

## 🐛 Known Issues

- None currently identified in beta testing

## ✨ Changelog

### v2.0.0-beta.3 (Latest)

#### Added
- **Menu-based configuration flow** with four sections
- **AWS Configuration menu** for managing credentials and region
- **Automatic integration reload** after all configuration changes
- **Intelligent navigation** from AWS config to AI config
- **Region-first field ordering** to emphasize impact on model availability
- Clear descriptions for all configuration options
- Helpful guidance about automatic reloads

#### Changed
- Reorganized options flow into logical sections
- Improved user experience with automatic navigation
- Enhanced configuration descriptions
- Better feedback on what happens when saving

#### Fixed
- Configuration changes now take effect immediately
- Model list updates correctly after region changes
- No more manual reload needed after configuration changes

### v2.0.0-beta.2

#### Added
- Configurable memory guidelines in UI
- Multi-language support for memory instructions
- Automatic retry mechanism for Bedrock validation errors

#### Changed
- All blocking I/O moved to executor threads

#### Fixed
- Event loop blocking warnings eliminated
- Corrupted session file handling
- Code quality issues (ruff, mypy, pylint)

### v2.0.0-beta.1

#### Added
- Strands SDK integration
- Three-tier memory system
- Multi-user session management
- Enhanced Home Assistant device control
- Comprehensive documentation

#### Changed
- Complete architectural refactoring
- Improved error handling and logging
- Better async/await patterns

#### Removed
- Bedrock Agent support (temporary)
- Knowledge Base integration (temporary)

## 🙏 Acknowledgments

This release builds on:
- [Strands Agents SDK](https://github.com/strands-agents/sdk-python) by AWS
- [Mem0](https://github.com/mem0ai/mem0) for semantic memory
- [FAISS](https://github.com/facebookresearch/faiss) by Meta for vector search
- Home Assistant conversation and intent systems

## 🔗 Links

- [Documentation](https://github.com/your-repo/blob/main/README.md)
- [Issue Tracker](https://github.com/your-repo/issues)
- [Discussions](https://github.com/your-repo/discussions)

---

**Thank you for testing this beta release!** Your feedback helps make this integration better for everyone. 🎉
