# Website Test Suite

Comprehensive test coverage for the primary-assistant website application.

## Test Files

### `test_gemini_service_migration.py`

Unit tests for the migration from `google.generativeai` to `google.genai` SDK.

**Test Coverage:**
- ✅ Client initialization (API key from parameter, environment, error handling)
- ✅ Safety settings format (list vs dict, string values vs enums)
- ✅ History building (dict to Content objects conversion)
- ✅ System instruction contextualization (current date injection)
- ✅ Chat method (client.chats.create, automatic_function_calling disabled)
- ✅ Response extraction (response.text property, response.function_calls)
- ✅ API key validation
- ✅ Model fallback on quota errors
- ✅ Function calling (single and multiple)
- ✅ Integration scenarios

**Total Tests:** 35+ comprehensive test cases across 8 test classes

## Running Tests

### Prerequisites

Install pytest if not already installed:

```bash
pip install pytest pytest-cov
```

### Run All Tests

```bash
# From website directory
cd /Users/nathanbowman/primary-assistant/website
pytest tests/

# With verbose output
pytest tests/ -v

# With coverage report
pytest tests/ --cov=services --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/test_gemini_service_migration.py -v
```

### Run Specific Test Class

```bash
pytest tests/test_gemini_service_migration.py::TestClientInitialization -v
```

### Run Specific Test Method

```bash
pytest tests/test_gemini_service_migration.py::TestClientInitialization::test_client_initialization_with_api_key_parameter -v
```

### Run with Output

```bash
# Show print statements
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l
```

## Test Structure

```
tests/
├── __init__.py                           # Package marker
├── README.md                             # This file
└── test_gemini_service_migration.py      # GenAI SDK migration tests
    ├── TestClientInitialization          # 5 tests
    ├── TestSafetySettings                # 4 tests
    ├── TestHistoryBuilding               # 4 tests
    ├── TestSystemInstruction             # 3 tests
    ├── TestChatMethod                    # 5 tests
    ├── TestResponseExtraction            # 6 tests
    ├── TestAPIKeyValidation              # 2 tests
    ├── TestQuotaHandling                 # 5 tests
    └── TestIntegrationScenarios          # 2 tests
```

## Migration Testing Checklist

Before deploying the GenAI SDK migration:

- [ ] All unit tests pass
- [ ] Client initialization works with API key parameter
- [ ] Client initialization works with environment variable
- [ ] Safety settings return list of SafetySetting objects
- [ ] History converts to Content/Part objects correctly
- [ ] System instruction includes current date
- [ ] Chat creates client.chats.create() correctly
- [ ] Automatic function calling is disabled
- [ ] Response.text property is used
- [ ] Response.function_calls is extracted correctly
- [ ] Single function calls work
- [ ] Multiple function calls wrapped correctly
- [ ] Default messages provided when no text
- [ ] Model fallback triggers on quota error
- [ ] QuotaExhaustedError raised when all models exhausted
- [ ] API key validation works

## CI/CD Integration

Add to your deployment pipeline:

```bash
# Run tests before deployment
pytest tests/ --cov=services --cov-fail-under=80

# Only deploy if tests pass
if [ $? -eq 0 ]; then
    echo "Tests passed, deploying..."
else
    echo "Tests failed, aborting deployment"
    exit 1
fi
```

## Adding New Tests

When adding new functionality:

1. Create test file: `test_<module_name>.py`
2. Import required modules and mocks
3. Organize tests into classes by functionality
4. Use descriptive test method names: `test_<what_it_does>`
5. Follow AAA pattern: Arrange, Act, Assert
6. Mock external dependencies (API calls, database, etc.)
7. Test both success and failure cases
8. Update this README with new test coverage

## Common Issues

### Import Errors

If you get import errors, ensure you're running from the website directory:

```bash
cd /Users/nathanbowman/primary-assistant/website
export PYTHONPATH=/Users/nathanbowman/primary-assistant/website:$PYTHONPATH
pytest tests/
```

### Mocking Issues

The tests use `unittest.mock` extensively. Key patterns:

```python
# Mock module-level imports
@patch('website.services.gemini_service.genai')

# Mock environment variables
@patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'})

# Mock return values
mock_client.method.return_value = Mock()

# Mock side effects (exceptions, sequences)
mock_client.method.side_effect = Exception("Error")
```

## References

- Migration Plan: `/Users/nathanbowman/.claude/plans/silly-tinkering-llama.md`
- Service Being Tested: `/Users/nathanbowman/primary-assistant/website/services/gemini_service.py`
- pytest Documentation: https://docs.pytest.org/
- unittest.mock Guide: https://docs.python.org/3/library/unittest.mock.html
