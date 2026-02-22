# Release Notes - Amazon Bedrock Agent Integration

## Known Issues

### Protobuf Dependency Conflict with apple_tv and esphome

**Issue:** When installing the bedrock_agent component with mem0_memory support, a protobuf version conflict may occur if you're also using the `apple_tv` or `esphome` integrations.

**Root Cause:** 
- `mem0ai` (used for long-term memory) requires `protobuf>=5.29.0,<6.0.0`
- `pyatv==0.17.0` (apple_tv) requires `protobuf>=6.31.1`
- `aioesphomeapi==43.14.0` (esphome) requires `protobuf>=6,<8`

This creates an incompatible dependency tree where pip cannot satisfy all requirements simultaneously.

**Workaround:**

To use all three integrations together, follow this installation sequence:

1. Install strands dependencies first:
   ```bash
   pip install strands-agents-tools
   pip install strands-agents-tools[mem0_memory]
   ```

2. Upgrade aioesphomeapi to the latest version:
   ```bash
   pip install aioesphomeapi==44.0.0
   ```

The newer version of aioesphomeapi (44.0.0) is compatible with the protobuf version constraints, allowing all components to coexist.

**Alternative:** If you don't need the long-term memory feature, you can remove the `strands-agents-tools[mem0_memory]` extra from the manifest.json file, which will prevent mem0ai from being installed and avoid the conflict entirely.

**Status:** This is a known upstream dependency issue. We're monitoring mem0ai releases for updates that support protobuf 6+.

---

## Version History

### Current Version
- Updated dependencies to latest stable versions
- Added support for mem0_memory long-term semantic memory
- Improved session management and user isolation
- Enhanced error handling for conversation blocks
