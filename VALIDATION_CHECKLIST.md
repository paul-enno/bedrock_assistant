# Bedrock Agent Refactoring Validation Checklist

## Pre-Deployment Validation

### Code Quality
- [ ] Run mypy type checking
  ```bash
  mypy homeassistant/components/bedrock_agent/
  ```

- [ ] Run pylint
  ```bash
  pylint homeassistant/components/bedrock_agent/
  ```

- [ ] Run ruff formatting check
  ```bash
  ruff check homeassistant/components/bedrock_agent/
  ```

- [ ] Check for syntax errors
  ```bash
  python -m py_compile homeassistant/components/bedrock_agent/*.py
  ```

### Testing
- [ ] Run all unit tests
  ```bash
  pytest tests/components/bedrock_agent/
  ```

- [ ] Run tests with coverage
  ```bash
  pytest --cov=homeassistant.components.bedrock_agent \
         --cov-report=term-missing \
         tests/components/bedrock_agent/
  ```

- [ ] Run quick test on changed files
  ```bash
  pytest --timeout=10 --picked tests/components/bedrock_agent/
  ```

- [ ] Verify no test failures
- [ ] Check coverage percentage (target: >80%)

### Integration Validation
- [ ] Test config entry setup
- [ ] Test config entry unload
- [ ] Test conversation agent registration
- [ ] Test service registration
- [ ] Test options update

### Functional Testing
- [ ] Test conversation with foundation model
- [ ] Test conversation with custom agent (if available)
- [ ] Test cognitive_task service with text only
- [ ] Test cognitive_task service with image file
- [ ] Test cognitive_task service with image URL
- [ ] Test error handling (invalid credentials, etc.)

### Documentation
- [ ] Review ARCHITECTURE.md
- [ ] Review REFACTORING.md
- [ ] Review test README.md
- [ ] Update component docstrings if needed

## Post-Deployment Validation

### Monitoring
- [ ] Check logs for errors
- [ ] Monitor AWS API calls
- [ ] Check conversation response times
- [ ] Verify service calls work

### User Experience
- [ ] Test in Home Assistant UI
- [ ] Verify conversation agent appears
- [ ] Test voice assistant integration
- [ ] Verify service appears in Developer Tools

### Rollback Plan
- [ ] Document rollback procedure
- [ ] Keep backup of old code
- [ ] Test rollback process

## Test Commands Reference

### Run all tests
```bash
pytest tests/components/bedrock_agent/
```

### Run specific test file
```bash
pytest tests/components/bedrock_agent/test_agent.py
```

### Run specific test
```bash
pytest tests/components/bedrock_agent/test_agent.py::test_agent_initialization
```

### Run with verbose output
```bash
pytest -v tests/components/bedrock_agent/
```

### Run with coverage
```bash
pytest --cov=homeassistant.components.bedrock_agent \
       --cov-report=html \
       tests/components/bedrock_agent/
```

### Run with debugging
```bash
pytest -vv -s tests/components/bedrock_agent/
```

## Expected Test Results

### Coverage Targets
- Overall coverage: >80%
- Critical paths: 100%
  - Agent initialization
  - Conversation processing
  - Service handlers
  - Error handling

### Test Count
- Minimum 30+ test cases across 7 test files
- All tests should pass
- No skipped tests (unless intentional)

## Known Issues to Watch

### Potential Issues
1. Mock configuration in tests
2. Async executor job handling
3. boto3 client creation timing
4. Session manager file permissions
5. Image file path validation

### Mitigation
- Comprehensive fixtures in conftest.py
- Proper async/await usage
- Clear mock boundaries
- Configurable storage paths
- Thorough path validation tests

## Sign-off

- [ ] All tests pass
- [ ] Code quality checks pass
- [ ] Documentation complete
- [ ] Functional testing complete
- [ ] Ready for deployment

## Notes

Add any observations or issues discovered during validation:

```
[Space for notes]
```
