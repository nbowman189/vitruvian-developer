# GenAI SDK Migration Test Checklist

This checklist ensures the migration from `google.generativeai` to `google.genai` SDK is validated thoroughly before deployment.

## Pre-Migration Checklist

- [ ] Backup current `gemini_service.py`
- [ ] Document current functionality
- [ ] Review migration plan at `/Users/nathanbowman/.claude/plans/silly-tinkering-llama.md`
- [ ] Install pytest: `pip install pytest pytest-cov`

## Test Execution

### 1. Run Unit Tests

```bash
cd /Users/nathanbowman/primary-assistant/website
pytest tests/test_gemini_service_migration.py -v
```

**Expected:** All 35 tests pass

### 2. Verify Test Coverage by Category

#### Client Initialization (4 tests)
- [ ] `test_client_initialization_with_api_key_parameter` - PASS
- [ ] `test_client_initialization_with_environment_variable` - PASS
- [ ] `test_client_initialization_raises_error_when_api_key_missing` - PASS
- [ ] `test_client_initialization_stores_model_fallback_chain` - PASS

#### Safety Settings (4 tests)
- [ ] `test_safety_settings_returns_list_not_dict` - PASS
- [ ] `test_safety_settings_includes_all_four_harm_categories` - PASS
- [ ] `test_safety_settings_creates_safety_setting_objects` - PASS
- [ ] `test_safety_settings_uses_string_values_not_enums` - PASS

#### History Building (4 tests)
- [ ] `test_build_history_converts_dicts_to_content_objects` - PASS
- [ ] `test_build_history_maps_roles_correctly` - PASS
- [ ] `test_build_history_uses_part_from_text` - PASS
- [ ] `test_build_history_handles_empty_history` - PASS

#### System Instruction (3 tests)
- [ ] `test_system_instruction_includes_current_date` - PASS
- [ ] `test_system_instruction_includes_day_of_week` - PASS
- [ ] `test_system_instruction_format_matches_expected_pattern` - PASS

#### Chat Method (5 tests)
- [ ] `test_chat_successful_with_simple_message` - PASS
- [ ] `test_chat_with_function_declarations` - PASS
- [ ] `test_chat_disables_automatic_function_calling` - PASS
- [ ] `test_chat_falls_back_on_quota_error` - PASS
- [ ] `test_chat_raises_quota_exhausted_when_all_models_fail` - PASS

#### Response Extraction (6 tests)
- [ ] `test_extract_response_uses_text_property` - PASS
- [ ] `test_extract_response_extracts_function_calls` - PASS
- [ ] `test_extract_response_handles_single_function_call` - PASS
- [ ] `test_extract_response_wraps_multiple_function_calls` - PASS
- [ ] `test_extract_response_provides_default_message_for_function_only` - PASS
- [ ] `test_extract_response_provides_count_message_for_multiple_functions` - PASS

#### API Key Validation (2 tests)
- [ ] `test_validate_api_key_with_valid_key` - PASS
- [ ] `test_validate_api_key_with_invalid_key` - PASS

#### Quota Handling (5 tests)
- [ ] `test_is_quota_error_detects_429_status` - PASS
- [ ] `test_is_quota_error_detects_quota_keyword` - PASS
- [ ] `test_is_quota_error_detects_rate_limit` - PASS
- [ ] `test_extract_retry_delay_parses_seconds` - PASS
- [ ] `test_extract_retry_delay_defaults_to_3600` - PASS

#### Integration Scenarios (2 tests)
- [ ] `test_simple_conversation_without_functions` - PASS
- [ ] `test_conversation_with_function_call` - PASS

### 3. Run with Coverage

```bash
pytest tests/test_gemini_service_migration.py --cov=services.gemini_service --cov-report=html --cov-report=term-missing
```

**Expected:** 80%+ code coverage

### 4. Test Specific Scenarios

Run these commands to test individual scenarios:

```bash
# Test client initialization only
pytest tests/test_gemini_service_migration.py::TestClientInitialization -v

# Test safety settings only
pytest tests/test_gemini_service_migration.py::TestSafetySettings -v

# Test chat method only
pytest tests/test_gemini_service_migration.py::TestChatMethod -v

# Test function calling
pytest tests/test_gemini_service_migration.py::TestResponseExtraction -v
```

## Post-Migration Manual Testing

After code migration, test these scenarios manually:

### 1. Simple Chat
```bash
# Start the application
docker-compose up -d

# Navigate to AI Coach page
# http://localhost:8001/ai-coach

# Test message: "Hello"
# Expected: Friendly greeting from coach
```
- [ ] Simple chat works - PASS
- [ ] Response is coherent - PASS
- [ ] No errors in logs - PASS

### 2. Single Function Call
```bash
# Test message: "I weighed 176 lbs today"
# Expected: create_health_metric function call card
```
- [ ] Function call detected - PASS
- [ ] Arguments correct (weight: 176, date: today) - PASS
- [ ] Can review and save record - PASS
- [ ] Record appears in database - PASS

### 3. Multiple Function Calls
```bash
# Test message: "I weighed 176lbs, did a 60min workout, and ate breakfast (650 cal, 45g protein)"
# Expected: 3 function calls (health, workout, meal)
```
- [ ] All 3 function calls detected - PASS
- [ ] Wrapped in multiple_function_calls structure - PASS
- [ ] Can review all records - PASS
- [ ] All records save correctly - PASS

### 4. READ Function (Data Query)
```bash
# Test message: "How am I doing with my weight?"
# Expected: get_recent_health_metrics called, data-driven response
```
- [ ] READ function called automatically - PASS
- [ ] Results injected into context - PASS
- [ ] Response references actual data - PASS
- [ ] No errors - PASS

### 5. Model Fallback
```bash
# Simulate quota exhaustion (requires API manipulation)
# Expected: Automatic fallback to next model
```
- [ ] Fallback triggers on quota error - PASS
- [ ] Second model used successfully - PASS
- [ ] User sees seamless experience - PASS

## API Compatibility Verification

### Check All 14 Functions Work

**WRITE Functions (6):**
- [ ] `create_health_metric` - Weight, body fat logging
- [ ] `create_meal_log` - Nutrition tracking
- [ ] `create_workout` - Workout sessions
- [ ] `create_coaching_session` - Coaching notes
- [ ] `create_behavior_definition` - Behavior tracking setup
- [ ] `log_behavior` - Daily behavior completion

**READ Functions (8):**
- [ ] `get_recent_health_metrics` - Weight trends
- [ ] `get_workout_history` - Recent workouts
- [ ] `get_nutrition_summary` - Meal analysis
- [ ] `get_user_goals` - Goal tracking
- [ ] `get_coaching_history` - Past sessions
- [ ] `get_progress_summary` - Comprehensive overview
- [ ] `get_behavior_tracking` - Behavior completion
- [ ] `get_behavior_plan_compliance` - Adherence analysis

## Critical Validations

### 1. Automatic Function Calling is DISABLED
```python
# In gemini_service.py, verify this code exists:
config.automatic_function_calling = types.AutomaticFunctionCallingConfig(disable=True)
```
- [ ] Code present - VERIFIED
- [ ] Functions NOT auto-executed - VERIFIED
- [ ] User approval required - VERIFIED

### 2. Safety Settings Format
```python
# Verify safety settings are a LIST, not dict:
[
    types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_MEDIUM_AND_ABOVE'),
    # ... 3 more
]
```
- [ ] Returns list - VERIFIED
- [ ] Uses SafetySetting objects - VERIFIED
- [ ] String values (not enums) - VERIFIED

### 3. History Format
```python
# Verify history uses Content/Part objects:
history = [
    types.Content(role='user', parts=[types.Part.from_text('Hello')]),
    types.Content(role='model', parts=[types.Part.from_text('Hi')])
]
```
- [ ] Content objects used - VERIFIED
- [ ] Part.from_text() used - VERIFIED
- [ ] Role mapping correct (assistant → model) - VERIFIED

### 4. Response Properties
```python
# Verify response uses convenience properties:
text = response.text  # Not manual extraction from candidates
function_calls = response.function_calls  # Direct access
```
- [ ] response.text used - VERIFIED
- [ ] response.function_calls used - VERIFIED
- [ ] No manual candidate parsing - VERIFIED

## Performance Validation

- [ ] Response time similar to old SDK (< 3s typical)
- [ ] No memory leaks over 100+ messages
- [ ] Quota fallback < 1s overhead
- [ ] No degradation in conversation quality

## Error Handling

- [ ] Invalid API key shows clear error
- [ ] Quota exhaustion shows user-friendly message
- [ ] Network errors handled gracefully
- [ ] Malformed function calls don't crash app

## Deployment Checklist

- [ ] All unit tests pass (35/35)
- [ ] Coverage > 80%
- [ ] Manual testing complete (all scenarios)
- [ ] All 14 functions tested
- [ ] Performance validated
- [ ] Error handling verified
- [ ] Backup of old code saved
- [ ] Rollback plan documented
- [ ] Monitoring configured
- [ ] Logs reviewed for warnings

## Rollback Plan

If issues are found:

```bash
# Option 1: Git revert
git checkout main -- website/services/gemini_service.py website/requirements.txt
docker-compose down && docker-compose up -d --build

# Option 2: Package rollback
pip uninstall google-genai
pip install google-generativeai==0.8.6
# Restart containers
```

## Success Criteria

Migration is successful when:
- ✅ All 35 unit tests pass
- ✅ All 14 AI functions work (6 WRITE + 8 READ)
- ✅ Single and multiple function calls work
- ✅ Model fallback works on quota errors
- ✅ Automatic function calling is disabled
- ✅ Response quality unchanged
- ✅ Performance metrics similar
- ✅ No new errors in production logs

## Sign-off

- [ ] Developer tested: _________________ Date: _______
- [ ] Unit tests passed: ________________ Date: _______
- [ ] Manual tests passed: ______________ Date: _______
- [ ] Ready for deployment: _____________ Date: _______

---

**Migration Plan:** `/Users/nathanbowman/.claude/plans/silly-tinkering-llama.md`
**Test File:** `/Users/nathanbowman/primary-assistant/website/tests/test_gemini_service_migration.py`
**Service:** `/Users/nathanbowman/primary-assistant/website/services/gemini_service.py`
