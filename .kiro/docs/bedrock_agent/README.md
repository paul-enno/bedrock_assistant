# Bedrock Agent Integration Documentation

This directory contains development documentation for the Home Assistant Bedrock Agent integration.

## Documentation Files

### Architecture & Design
- **ARCHITECTURE.md** - Overall architecture and component design
- **REFACTORING.md** - Refactoring history and improvements

### Memory System
- **MEMORY.md** - Memory system overview
- **MEMORY_CONFIGURATION.md** - How to configure memory features
- **MEMORY_OPTIONS.md** - Available memory configuration options
- **MEM0_IMPLEMENTATION.md** - Mem0 integration implementation details
- **MEM0_CREDENTIALS.md** - Mem0 AWS credentials configuration
- **MEM0_CREDENTIALS_SUMMARY.md** - Summary of credential setup
- **MEM0_QUICK_START.md** - Quick start guide for memory features
- **MEM0_SUMMARY.md** - Summary of Mem0 integration
- **MULTI_USER_SUPPORT.md** - Multi-user memory isolation
- **USER_ID_IMPLEMENTATION.md** - User ID implementation details

### Home Assistant Control
- **HA_CONTROL.md** - Home Assistant device control integration

### Dependencies
- **DEPENDENCIES.md** - External dependencies and requirements

### Archived Code
- **ARCHIVED_BEDROCK_SDK_CODE.md** - Original Bedrock SDK implementation (knowledge bases and agents)

## Purpose

These documents were created during development to:
- Document design decisions
- Explain implementation details
- Provide usage guides
- Track refactoring history
- Archive deprecated code for potential future use

They are not required for the integration to function and are kept here for reference and future development.

## Integration Location

The actual integration code is located at:
`homeassistant/components/bedrock_agent/`

## Current Implementation

The integration now uses:
- **Strands SDK** for agent management and tool integration
- **Mem0** for long-term semantic memory with FAISS storage
- **Home Assistant LLM API** for device control and smart home integration
- **AWS Bedrock** for foundation models (Claude, Titan, etc.)

## Archived Features

The following features were removed on February 18, 2026 and archived in `ARCHIVED_BEDROCK_SDK_CODE.md`:

### What Was Removed
- Direct Bedrock Agent invocation via `bedrock-agent-runtime` SDK
- Knowledge Base integration and configuration
- Agent ID and Alias ID configuration fields
- `async_call_bedrock_agent()` method
- `get_knowledgebases_selectOptionDict()` and `get_agents_selectOptionDict()` functions

### Why It Was Removed
These features were replaced with the Strands SDK approach which provides:
- Better tool integration and management
- Simplified agent configuration
- More flexible memory management with Mem0
- Easier maintenance and extensibility

### Potential Revival
The archived code is preserved in case these features need to be revived in the future. The code includes:
- Constants for knowledge base and agent configuration
- AWS client factory methods for bedrock-agent-runtime
- Agent invocation logic
- Config flow functions for listing knowledge bases and agents

If you need to restore these features, refer to `ARCHIVED_BEDROCK_SDK_CODE.md` for the complete implementation.

## Configuration Options

The integration currently supports:
- AWS credentials (access key, secret key, region)
- Model selection (Claude, Titan, etc.)
- Memory enablement toggle
- Home Assistant control toggle
- Memory storage path configuration
- Temperature and max tokens settings

## Development Notes

When making changes to the integration:
1. Update relevant documentation files in this directory
2. Keep the README in sync with major architectural changes
3. Archive deprecated code rather than deleting it
4. Document the reasoning behind significant refactoring decisions
