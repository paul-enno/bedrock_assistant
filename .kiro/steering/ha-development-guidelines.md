---
inclusion: auto
---

# Home Assistant Development Guidelines - Knowledge Base Reference

This steering document references the local dev-docs knowledge base for Home Assistant development standards and best practices.

## Knowledge Base Location

All detailed documentation is available in: `dev-docs/homeassistant/docs/`

## Core Development Guidelines

### Style and Code Quality

**Reference**: `dev-docs/homeassistant/docs/development_guidelines.md`

Key points:
- Strict PEP8 and PEP 257 compliance enforced via Ruff
- Comments must be full sentences ending with periods
- Imports must be ordered
- Constants and lists/dictionaries in alphabetical order
- Use f-strings for formatting (except logging which uses % formatting)
- Full typing encouraged - add to `.strict-typing` for strict checking
- File headers should be concise: `"""Support for MQTT lights."""`

### Logging Standards

- No platform/component names in log messages (added automatically)
- No periods at end of log messages
- Never log API keys, tokens, passwords
- Use `_LOGGER.debug` for non-user-facing messages
- Use lazy logging: `_LOGGER.info("Message %s", variable)`

### Component Checklist

**Reference**: `dev-docs/homeassistant/docs/creating_component_code_review.md`

Critical requirements:
1. Follow style guidelines
2. Use constants from `homeassistant.const`
3. Requirements in `manifest.json` with pinned versions
4. All API code in third-party PyPI library
5. Keep PRs small - single platform, no feature mixing
6. Prefix event names with domain
7. Add tests for all new code

### Async Programming

**Reference**: `dev-docs/homeassistant/docs/asyncio_blocking_operations.md`

All blocking operations MUST run in executor:

```python
# Blocking I/O - use executor
result = await hass.async_add_executor_job(blocking_function, args)
result = await hass.async_add_executor_job(partial(func, kwarg=True))

# Never block event loop
# ❌ requests.get(url)
# ✅ await hass.async_add_executor_job(requests.get, url)
```

Common blocking operations requiring executor:
- File I/O: `open`, `read`, `write`, `glob`, `os.walk`, `os.listdir`
- Network: `requests`, `urllib`, `urlopen`
- SSL: `SSLContext.load_default_certs`, `load_verify_locations`
- Image processing: `PIL.Image.open`
- Imports: `import_module` (see asyncio_imports.md)

Use `await asyncio.sleep()` instead of `time.sleep()`

### Config Flow Implementation

**Reference**: `dev-docs/homeassistant/docs/config_entries_config_flow_handler.md`

Requirements:
- Add `config_flow: true` to manifest
- Create `config_flow.py` extending `ConfigFlow`
- Set VERSION and MINOR_VERSION
- Implement required steps (user, discovery methods)
- Set unique IDs for discovered devices
- Test connection before setup
- Full test coverage required

Reserved step names:
- `user`: User-initiated setup
- `reauth`: Handle authentication failures
- `reconfigure`: Change config entry data
- `bluetooth`, `dhcp`, `homekit`, `mqtt`, `ssdp`, `usb`, `zeroconf`: Discovery

Unique ID requirements:
- Must be stable and unchangeable by user
- Acceptable: Serial number, MAC address, geo location
- Unacceptable: IP address, hostname, device name

### Integration Quality Scale

**Reference**: `dev-docs/homeassistant/docs/core/integration-quality-scale/index.md`

Four tiers: Bronze (minimum), Silver, Gold, Platinum

**Bronze** (required for all new integrations):
- UI-based setup via config flow
- Basic coding standards
- Automated config flow tests
- Basic documentation

**Silver**:
- Error handling and recovery
- Active code owner
- Reauthentication support
- Detailed documentation

**Gold**:
- Full feature support
- Automatic discovery
- Translations
- Extensive documentation
- Full test coverage
- Required for Works with Home Assistant

**Platinum**:
- Technical excellence
- Fully typed code
- Fully async
- Optimized performance

Track progress in `quality_scale.yaml`:
```yaml
rules:
  config_flow: done
  docs_high_level_description:
    status: exempt
    comment: Reason for exemption
```

## Integration-Specific Patterns

### AWS/Boto3 Integration

For integrations using boto3 (like bedrock_agent):

```python
# Client creation in executor
client = await hass.async_add_executor_job(
    partial(
        boto3.client,
        service_name="bedrock",
        region_name=region,
        aws_access_key_id=key_id,
        aws_secret_access_key=key_secret
    )
)

# API calls in executor
response = await hass.async_add_executor_job(
    partial(
        client.list_foundation_models,
        byOutputModality="TEXT"
    )
)
```

### Error Handling

Use specific exceptions:
- `ConfigEntryNotReady`: Temporary connection issues
- `ConfigEntryAuthFailed`: Authentication failures
- `HomeAssistantError`: General runtime errors
- `ServiceValidationError`: User input errors

Bare exceptions allowed ONLY in:
- Config flows (for robustness)
- Background tasks

Keep try blocks minimal:
```python
# ❌ Bad - processing inside try
try:
    data = await device.get_data()
    processed = data.get("value", 0) * 100
    self._attr_native_value = processed
except DeviceError:
    _LOGGER.error("Failed")

# ✅ Good - only risky code in try
try:
    data = await device.get_data()
except DeviceError:
    _LOGGER.error("Failed")
    return

processed = data.get("value", 0) * 100
self._attr_native_value = processed
```

### Testing Requirements

**Reference**: `dev-docs/homeassistant/docs/development_testing.md`

- Config flow: 100% test coverage required
- Integration code: >95% coverage for Silver tier
- Test connection validation errors
- Test all config flow steps
- Mock external services
- Use pytest with fixtures

Run tests:
```bash
# Quick test of changed files
pytest --timeout=10 --picked

# Specific integration
pytest tests/components/bedrock_agent/

# With coverage
pytest --cov=homeassistant.components.bedrock_agent
```

### Documentation Standards

**Reference**: `dev-docs/homeassistant/docs/documenting/standards.md`

- American English
- Sentence case for titles
- No two spaces after periods
- Use serial (Oxford) comma
- Backticks for: file paths, filenames, variables
- Clear step-by-step instructions
- Include prerequisites
- Provide removal instructions

## Development Commands

From workspace root (activate venv first if not in container):

```bash
# Linting
prek run --all-files          # All files
prek run                      # Staged files only

# Type checking
mypy homeassistant/components/bedrock_agent

# Testing
pytest --timeout=10 --picked  # Changed files
pytest tests/components/bedrock_agent/

# Update requirements
python -m script.gen_requirements_all

# Update translations
python -m script.translations develop --all

# Validate project structure
python -m script.hassfest
```

## Additional Resources

Detailed documentation available in dev-docs:

- **Architecture**: `dev-docs/homeassistant/docs/architecture/`
- **Entity Platform**: `dev-docs/homeassistant/docs/core/entity/`
- **Config Entries**: `dev-docs/homeassistant/docs/config_entries_*.md`
- **Data Flow**: `dev-docs/homeassistant/docs/data_entry_flow_index.md`
- **Device Registry**: `dev-docs/homeassistant/docs/device_registry_index.md`
- **Diagnostics**: `dev-docs/homeassistant/docs/core/integration_diagnostics.md`
- **LLM Integration**: `dev-docs/homeassistant/docs/core/llm/`
- **Translations**: `dev-docs/homeassistant/docs/internationalization/`
- **Quality Scale Rules**: `dev-docs/homeassistant/docs/core/integration-quality-scale/rules/`

## Quick Reference Checklist

Before submitting code:

- [ ] Follows PEP8/PEP 257 (run `prek run`)
- [ ] All blocking I/O in executor
- [ ] Type hints added
- [ ] Tests written (config flow 100% coverage)
- [ ] Translations in `strings.json`
- [ ] Documentation updated
- [ ] No sensitive data in logs
- [ ] Unique ID set for discoveries
- [ ] Error handling with specific exceptions
- [ ] `python -m script.hassfest` passes
- [ ] Requirements pinned in manifest.json
