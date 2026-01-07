"""
Comprehensive Unit Tests for Google GenAI SDK Migration
========================================================

Tests for the migration from google.generativeai to google.genai SDK.
Validates all critical changes in the GeminiService class.

Migration Plan Reference: /Users/nathanbowman/.claude/plans/silly-tinkering-llama.md
Service Being Tested: /Users/nathanbowman/primary-assistant/website/services/gemini_service.py

Test Coverage:
1. Client initialization (API key handling)
2. Safety settings format (list vs dict)
3. History building (dict to Content objects)
4. System instruction contextualization
5. Chat method (client.chats.create, automatic_function_calling)
6. Response extraction (response.text, response.function_calls)
7. API key validation
8. Model fallback on quota errors
9. Function calling (single and multiple)
"""

import os
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
from typing import List, Dict, Any

# Import the service to test
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestClientInitialization:
    """Test GeminiService client initialization with new google.genai SDK."""

    @patch('website.services.gemini_service.genai')
    def test_client_initialization_with_api_key_parameter(self, mock_genai):
        """Test that __init__ creates a genai.Client with API key from parameter."""
        from website.services.gemini_service import GeminiService

        # Create mock client
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client

        # Initialize service with API key
        service = GeminiService(api_key='test-api-key-123')

        # Verify Client was created with correct API key
        mock_genai.Client.assert_called_once_with(api_key='test-api-key-123')
        assert service.client == mock_client
        assert service.api_key == 'test-api-key-123'

    @patch('website.services.gemini_service.genai')
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'env-api-key-456'})
    def test_client_initialization_with_environment_variable(self, mock_genai):
        """Test that __init__ creates a genai.Client with API key from environment."""
        from website.services.gemini_service import GeminiService

        mock_client = Mock()
        mock_genai.Client.return_value = mock_client

        # Initialize service without API key parameter
        service = GeminiService()

        # Verify Client was created with API key from environment
        mock_genai.Client.assert_called_once_with(api_key='env-api-key-456')
        assert service.client == mock_client
        assert service.api_key == 'env-api-key-456'

    @patch('website.services.gemini_service.genai')
    @patch.dict(os.environ, {}, clear=True)
    def test_client_initialization_raises_error_when_api_key_missing(self, mock_genai):
        """Test that __init__ raises ValueError when API key is not provided."""
        from website.services.gemini_service import GeminiService

        # Ensure GEMINI_API_KEY is not in environment
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']

        # Attempt to initialize without API key
        with pytest.raises(ValueError) as exc_info:
            GeminiService()

        assert 'GEMINI_API_KEY not found' in str(exc_info.value)

    @patch('website.services.gemini_service.genai')
    def test_client_initialization_stores_model_fallback_chain(self, mock_genai):
        """Test that __init__ stores the model fallback chain correctly."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        # Verify model_names contains expected models in correct order
        assert isinstance(service.model_names, list)
        assert len(service.model_names) >= 2
        assert 'gemini-1.5-flash' in service.model_names
        assert 'gemini-1.5-flash-8b' in service.model_names


class TestSafetySettings:
    """Test _get_safety_settings() returns correct format for new SDK."""

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    def test_safety_settings_returns_list_not_dict(self, mock_types, mock_genai):
        """Test that _get_safety_settings() returns a list, not a dict."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        safety_settings = service._get_safety_settings()

        # Verify it's a list
        assert isinstance(safety_settings, list)
        assert not isinstance(safety_settings, dict)

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    def test_safety_settings_includes_all_four_harm_categories(self, mock_types, mock_genai):
        """Test that all 4 harm categories are included in safety settings."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()

        # Mock SafetySetting class
        mock_safety_setting = Mock()
        mock_types.SafetySetting.return_value = mock_safety_setting

        service = GeminiService(api_key='test-key')
        safety_settings = service._get_safety_settings()

        # Verify we have 4 safety settings
        assert len(safety_settings) == 4

        # Verify SafetySetting was called 4 times
        assert mock_types.SafetySetting.call_count == 4

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    def test_safety_settings_creates_safety_setting_objects(self, mock_types, mock_genai):
        """Test that each setting is a types.SafetySetting object."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()

        # Mock SafetySetting to return a specific object
        mock_safety_setting = Mock()
        mock_types.SafetySetting.return_value = mock_safety_setting

        service = GeminiService(api_key='test-key')
        safety_settings = service._get_safety_settings()

        # Verify all items are the SafetySetting mock
        for setting in safety_settings:
            assert setting == mock_safety_setting

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    def test_safety_settings_uses_string_values_not_enums(self, mock_types, mock_genai):
        """Test that category and threshold are strings, not enums."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')
        service._get_safety_settings()

        # Check that SafetySetting was called with string arguments
        for call_args in mock_types.SafetySetting.call_args_list:
            kwargs = call_args[1]
            assert isinstance(kwargs['category'], str)
            assert isinstance(kwargs['threshold'], str)
            # Verify they look like the expected format
            assert 'HARM_CATEGORY_' in kwargs['category']
            assert 'BLOCK_' in kwargs['threshold']


class TestHistoryBuilding:
    """Test _build_history() converts dict messages to types.Content objects."""

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    def test_build_history_converts_dicts_to_content_objects(self, mock_types, mock_genai):
        """Test that _build_history() converts dict messages to Content objects."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()

        # Mock Content and Part classes
        mock_content = Mock()
        mock_types.Content.return_value = mock_content
        mock_part = Mock()
        mock_types.Part.from_text.return_value = mock_part

        service = GeminiService(api_key='test-key')

        history = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there'}
        ]

        result = service._build_history(history)

        # Verify result is a list
        assert isinstance(result, list)

        # Verify Content was called for each message
        # (Note: might be called more times for system prompt)
        assert mock_types.Content.call_count >= len(history)

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    def test_build_history_maps_roles_correctly(self, mock_types, mock_genai):
        """Test that user → user and assistant → model role mapping works."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        mock_types.Content.return_value = Mock()
        mock_types.Part.from_text.return_value = Mock()

        service = GeminiService(api_key='test-key')

        history = [
            {'role': 'user', 'content': 'User message'},
            {'role': 'assistant', 'content': 'Assistant message'}
        ]

        service._build_history(history)

        # Check role mapping in Content calls
        content_calls = mock_types.Content.call_args_list
        user_roles = [call[1]['role'] for call in content_calls if 'role' in call[1]]

        # Should have both 'user' and 'model' roles
        assert 'user' in user_roles
        assert 'model' in user_roles

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    def test_build_history_uses_part_from_text(self, mock_types, mock_genai):
        """Test that _build_history() uses types.Part.from_text() for message content."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        mock_types.Content.return_value = Mock()
        mock_part = Mock()
        mock_types.Part.from_text.return_value = mock_part

        service = GeminiService(api_key='test-key')

        history = [{'role': 'user', 'content': 'Test message'}]
        service._build_history(history)

        # Verify Part.from_text was called
        assert mock_types.Part.from_text.call_count >= 1

        # Verify it was called with message content
        from_text_calls = [call[0][0] for call in mock_types.Part.from_text.call_args_list]
        assert any('Test message' in call for call in from_text_calls)

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    def test_build_history_handles_empty_history(self, mock_types, mock_genai):
        """Test that _build_history() handles empty conversation history."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        mock_types.Content.return_value = Mock()
        mock_types.Part.from_text.return_value = Mock()

        service = GeminiService(api_key='test-key')

        # Build history with no messages
        result = service._build_history([])

        # Should return a list (may contain system prompt)
        assert isinstance(result, list)


class TestSystemInstruction:
    """Test _get_contextualized_system_instruction() includes current date."""

    @patch('website.services.gemini_service.genai')
    def test_system_instruction_includes_current_date(self, mock_genai):
        """Test that system instruction includes current date."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        instruction = service._get_contextualized_system_instruction()

        # Verify current date is in the instruction
        current_date = datetime.now().strftime('%Y-%m-%d')
        assert current_date in instruction

    @patch('website.services.gemini_service.genai')
    def test_system_instruction_includes_day_of_week(self, mock_genai):
        """Test that system instruction includes day of week."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        instruction = service._get_contextualized_system_instruction()

        # Verify day of week is in the instruction
        day_of_week = datetime.now().strftime('%A')
        assert day_of_week in instruction

    @patch('website.services.gemini_service.genai')
    def test_system_instruction_format_matches_expected_pattern(self, mock_genai):
        """Test that system instruction starts with CURRENT DATE."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        instruction = service._get_contextualized_system_instruction()

        # Verify format
        assert instruction.startswith('CURRENT DATE:')
        assert 'IMPORTANT:' in instruction
        assert 'Transformative Trainer' in instruction or 'trainer' in instruction.lower()


class TestChatMethod:
    """Test chat() method with new client.chats.create() API."""

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    def test_chat_successful_with_simple_message(self, mock_types, mock_genai):
        """Test successful chat with a simple user message."""
        from website.services.gemini_service import GeminiService

        # Setup mocks
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client

        mock_chat = Mock()
        mock_client.chats.create.return_value = mock_chat

        mock_response = Mock()
        mock_response.text = "Hello! How can I help you today?"
        mock_response.function_calls = None
        mock_chat.send_message.return_value = mock_response

        # Mock types
        mock_types.Content.return_value = Mock()
        mock_types.Part.from_text.return_value = Mock()
        mock_types.SafetySetting.return_value = Mock()

        # Initialize service and chat
        service = GeminiService(api_key='test-key')
        response, function_call = service.chat("Hello", [])

        # Verify chat was created
        mock_client.chats.create.assert_called_once()

        # Verify send_message was called
        mock_chat.send_message.assert_called_once_with(message="Hello")

        # Verify response
        assert response == "Hello! How can I help you today?"
        assert function_call is None

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    def test_chat_with_function_declarations(self, mock_types, mock_genai):
        """Test chat with function declarations provided."""
        from website.services.gemini_service import GeminiService

        # Setup mocks
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client

        mock_chat = Mock()
        mock_client.chats.create.return_value = mock_chat

        mock_response = Mock()
        mock_response.text = "I'll log that for you."
        mock_response.function_calls = None
        mock_chat.send_message.return_value = mock_response

        # Mock types
        mock_config = Mock()
        mock_types.GenerateContentConfig.return_value = mock_config
        mock_types.Content.return_value = Mock()
        mock_types.Part.from_text.return_value = Mock()
        mock_types.SafetySetting.return_value = Mock()

        # Function declarations
        functions = [
            {'name': 'create_health_metric', 'description': 'Log health data'}
        ]

        # Initialize service and chat
        service = GeminiService(api_key='test-key')
        service.chat("I weigh 175 lbs", [], function_declarations=functions)

        # Verify GenerateContentConfig was created
        assert mock_types.GenerateContentConfig.called

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    def test_chat_disables_automatic_function_calling(self, mock_types, mock_genai):
        """Test that automatic_function_calling is disabled in config."""
        from website.services.gemini_service import GeminiService

        # Setup mocks
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client

        mock_chat = Mock()
        mock_client.chats.create.return_value = mock_chat

        mock_response = Mock()
        mock_response.text = "Response"
        mock_response.function_calls = None
        mock_chat.send_message.return_value = mock_response

        # Mock types
        mock_config = Mock()
        mock_types.GenerateContentConfig.return_value = mock_config
        mock_types.Content.return_value = Mock()
        mock_types.Part.from_text.return_value = Mock()
        mock_types.SafetySetting.return_value = Mock()
        mock_auto_fc_config = Mock()
        mock_types.AutomaticFunctionCallingConfig.return_value = mock_auto_fc_config

        # Initialize service and chat
        service = GeminiService(api_key='test-key')
        service.chat("Test", [])

        # Verify AutomaticFunctionCallingConfig was called with disable=True
        mock_types.AutomaticFunctionCallingConfig.assert_called_with(disable=True)

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    @patch('website.services.gemini_service.quota_manager')
    def test_chat_falls_back_on_quota_error(self, mock_quota_manager, mock_types, mock_genai):
        """Test model fallback when first model hits quota."""
        from website.services.gemini_service import GeminiService

        # Setup mocks
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client

        # First chat creation fails with quota error
        mock_chat1 = Mock()
        quota_error = Exception("429 Resource exhausted")
        mock_chat1.send_message.side_effect = quota_error

        # Second chat creation succeeds
        mock_chat2 = Mock()
        mock_response = Mock()
        mock_response.text = "Success with fallback model"
        mock_response.function_calls = None
        mock_chat2.send_message.return_value = mock_response

        # Return different chats for each call
        mock_client.chats.create.side_effect = [mock_chat1, mock_chat2]

        # Mock types
        mock_types.Content.return_value = Mock()
        mock_types.Part.from_text.return_value = Mock()
        mock_types.SafetySetting.return_value = Mock()
        mock_types.GenerateContentConfig.return_value = Mock()
        mock_types.AutomaticFunctionCallingConfig.return_value = Mock()

        # Mock quota manager
        mock_quota_manager.is_quota_available.return_value = True

        # Initialize service with multiple models
        service = GeminiService(api_key='test-key')
        service.model_names = ['gemini-1.5-flash', 'gemini-1.5-flash-8b']

        # Chat should succeed with fallback
        response, _ = service.chat("Test", [])

        # Verify both models were tried
        assert mock_client.chats.create.call_count == 2
        assert response == "Success with fallback model"

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    @patch('website.services.gemini_service.quota_manager')
    def test_chat_raises_quota_exhausted_when_all_models_fail(self, mock_quota_manager, mock_types, mock_genai):
        """Test QuotaExhaustedError when all models are exhausted."""
        from website.services.gemini_service import GeminiService, QuotaExhaustedError

        # Setup mocks
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client

        # All chats fail with quota error
        quota_error = Exception("429 Resource exhausted")
        mock_chat = Mock()
        mock_chat.send_message.side_effect = quota_error
        mock_client.chats.create.return_value = mock_chat

        # Mock types
        mock_types.Content.return_value = Mock()
        mock_types.Part.from_text.return_value = Mock()
        mock_types.SafetySetting.return_value = Mock()
        mock_types.GenerateContentConfig.return_value = Mock()
        mock_types.AutomaticFunctionCallingConfig.return_value = Mock()

        # Mock quota manager
        mock_quota_manager.is_quota_available.return_value = True
        mock_quota_manager.get_seconds_until_reset.return_value = 3600

        # Initialize service
        service = GeminiService(api_key='test-key')
        service.model_names = ['gemini-1.5-flash', 'gemini-1.5-flash-8b']

        # Should raise QuotaExhaustedError
        with pytest.raises(QuotaExhaustedError) as exc_info:
            service.chat("Test", [])

        assert "quota" in str(exc_info.value).lower()


class TestResponseExtraction:
    """Test _extract_response() uses response.text and response.function_calls."""

    @patch('website.services.gemini_service.genai')
    def test_extract_response_uses_text_property(self, mock_genai):
        """Test that _extract_response() uses response.text convenience property."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        # Create mock response with text property
        mock_response = Mock()
        mock_response.text = "This is the response text"
        mock_response.function_calls = None

        text, function_call = service._extract_response(mock_response)

        # Verify text property was used
        assert text == "This is the response text"
        assert function_call is None

    @patch('website.services.gemini_service.genai')
    def test_extract_response_extracts_function_calls(self, mock_genai):
        """Test extraction of function_calls from response."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        # Create mock function call
        mock_fc = Mock()
        mock_fc.name = 'create_health_metric'
        mock_fc.args = {'weight': 175, 'date': '2026-01-06'}

        # Create mock response
        mock_response = Mock()
        mock_response.text = ""
        mock_response.function_calls = [mock_fc]

        text, function_call = service._extract_response(mock_response)

        # Verify function call was extracted
        assert function_call is not None
        assert function_call['name'] == 'create_health_metric'
        assert function_call['args']['weight'] == 175

    @patch('website.services.gemini_service.genai')
    def test_extract_response_handles_single_function_call(self, mock_genai):
        """Test single function call handling."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        # Create single function call
        mock_fc = Mock()
        mock_fc.name = 'create_meal_log'
        mock_fc.args = {'meal_type': 'breakfast', 'calories': 650}

        mock_response = Mock()
        mock_response.text = "I've logged your breakfast."
        mock_response.function_calls = [mock_fc]

        text, function_call = service._extract_response(mock_response)

        # Verify single function call format
        assert function_call['name'] == 'create_meal_log'
        assert 'args' in function_call
        assert 'function_calls' not in function_call  # Not wrapped

    @patch('website.services.gemini_service.genai')
    def test_extract_response_wraps_multiple_function_calls(self, mock_genai):
        """Test multiple function calls are wrapped in special structure."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        # Create multiple function calls
        mock_fc1 = Mock()
        mock_fc1.name = 'create_health_metric'
        mock_fc1.args = {'weight': 176}

        mock_fc2 = Mock()
        mock_fc2.name = 'create_workout'
        mock_fc2.args = {'duration': 60}

        mock_fc3 = Mock()
        mock_fc3.name = 'create_meal_log'
        mock_fc3.args = {'calories': 650}

        mock_response = Mock()
        mock_response.text = ""
        mock_response.function_calls = [mock_fc1, mock_fc2, mock_fc3]

        text, function_call = service._extract_response(mock_response)

        # Verify multiple function calls are wrapped
        assert function_call['name'] == 'multiple_function_calls'
        assert 'function_calls' in function_call
        assert len(function_call['function_calls']) == 3

        # Verify individual calls
        calls = function_call['function_calls']
        assert calls[0]['name'] == 'create_health_metric'
        assert calls[1]['name'] == 'create_workout'
        assert calls[2]['name'] == 'create_meal_log'

    @patch('website.services.gemini_service.genai')
    def test_extract_response_provides_default_message_for_function_only(self, mock_genai):
        """Test default message when only function call, no text."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        # Function call with no text
        mock_fc = Mock()
        mock_fc.name = 'create_health_metric'
        mock_fc.args = {}

        mock_response = Mock()
        mock_response.text = ""  # Empty text
        mock_response.function_calls = [mock_fc]

        text, function_call = service._extract_response(mock_response)

        # Verify default message was provided
        assert len(text) > 0
        assert "prepared" in text.lower() or "review" in text.lower()

    @patch('website.services.gemini_service.genai')
    def test_extract_response_provides_count_message_for_multiple_functions(self, mock_genai):
        """Test default message mentions count for multiple function calls."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        # Multiple function calls with no text
        mock_fc1 = Mock()
        mock_fc1.name = 'create_health_metric'
        mock_fc1.args = {}

        mock_fc2 = Mock()
        mock_fc2.name = 'create_workout'
        mock_fc2.args = {}

        mock_response = Mock()
        mock_response.text = ""
        mock_response.function_calls = [mock_fc1, mock_fc2]

        text, function_call = service._extract_response(mock_response)

        # Verify count is mentioned
        assert "2" in text or "two" in text.lower()
        assert "records" in text.lower()


class TestAPIKeyValidation:
    """Test validate_api_key() static method."""

    @patch('website.services.gemini_service.genai')
    def test_validate_api_key_with_valid_key(self, mock_genai):
        """Test that valid API key returns True."""
        from website.services.gemini_service import GeminiService

        # Mock successful API call
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client

        mock_response = Mock()
        mock_response.text = "Test response"
        mock_client.models.generate_content.return_value = mock_response

        # Validate key
        result = GeminiService.validate_api_key('valid-api-key')

        # Verify
        assert result is True
        mock_genai.Client.assert_called_with(api_key='valid-api-key')

    @patch('website.services.gemini_service.genai')
    def test_validate_api_key_with_invalid_key(self, mock_genai):
        """Test that invalid API key returns False."""
        from website.services.gemini_service import GeminiService

        # Mock API error
        mock_genai.Client.side_effect = Exception("Invalid API key")

        # Validate key
        result = GeminiService.validate_api_key('invalid-key')

        # Verify
        assert result is False


class TestQuotaHandling:
    """Test quota error detection and model fallback."""

    @patch('website.services.gemini_service.genai')
    def test_is_quota_error_detects_429_status(self, mock_genai):
        """Test that _is_quota_error() detects 429 status code."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        error = Exception("429 Resource exhausted")
        assert service._is_quota_error(error) is True

    @patch('website.services.gemini_service.genai')
    def test_is_quota_error_detects_quota_keyword(self, mock_genai):
        """Test that _is_quota_error() detects 'quota' keyword."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        error = Exception("Quota exceeded for this API key")
        assert service._is_quota_error(error) is True

    @patch('website.services.gemini_service.genai')
    def test_is_quota_error_detects_rate_limit(self, mock_genai):
        """Test that _is_quota_error() detects rate limit errors."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        error = Exception("Rate limit exceeded")
        assert service._is_quota_error(error) is True

    @patch('website.services.gemini_service.genai')
    def test_extract_retry_delay_parses_seconds(self, mock_genai):
        """Test that _extract_retry_delay() parses retry seconds."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        error = Exception("retry_delay { seconds: 51 }")
        delay = service._extract_retry_delay(error)

        assert delay == 51

    @patch('website.services.gemini_service.genai')
    def test_extract_retry_delay_defaults_to_3600(self, mock_genai):
        """Test that _extract_retry_delay() defaults to 3600s (1 hour)."""
        from website.services.gemini_service import GeminiService

        mock_genai.Client.return_value = Mock()
        service = GeminiService(api_key='test-key')

        error = Exception("Some error without retry delay")
        delay = service._extract_retry_delay(error)

        assert delay == 3600


class TestIntegrationScenarios:
    """Integration tests for complete conversation flows."""

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    def test_simple_conversation_without_functions(self, mock_types, mock_genai):
        """Test a simple back-and-forth conversation."""
        from website.services.gemini_service import GeminiService

        # Setup mocks
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client

        mock_chat = Mock()
        mock_client.chats.create.return_value = mock_chat

        # First message
        mock_response1 = Mock()
        mock_response1.text = "Hello! I'm your fitness coach. How can I help?"
        mock_response1.function_calls = None

        # Second message
        mock_response2 = Mock()
        mock_response2.text = "Great! Let's track your progress."
        mock_response2.function_calls = None

        mock_chat.send_message.side_effect = [mock_response1, mock_response2]

        # Mock types
        mock_types.Content.return_value = Mock()
        mock_types.Part.from_text.return_value = Mock()
        mock_types.SafetySetting.return_value = Mock()
        mock_types.GenerateContentConfig.return_value = Mock()
        mock_types.AutomaticFunctionCallingConfig.return_value = Mock()

        # Initialize service
        service = GeminiService(api_key='test-key')

        # First message
        response1, fc1 = service.chat("Hello", [])
        assert "coach" in response1.lower()
        assert fc1 is None

        # Second message with history
        history = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': response1}
        ]
        response2, fc2 = service.chat("I want to track my weight", history)
        assert len(response2) > 0
        assert fc2 is None

    @patch('website.services.gemini_service.genai')
    @patch('website.services.gemini_service.types')
    def test_conversation_with_function_call(self, mock_types, mock_genai):
        """Test conversation that triggers a function call."""
        from website.services.gemini_service import GeminiService

        # Setup mocks
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client

        mock_chat = Mock()
        mock_client.chats.create.return_value = mock_chat

        # Mock function call
        mock_fc = Mock()
        mock_fc.name = 'create_health_metric'
        mock_fc.args = {
            'recorded_date': '2026-01-06',
            'weight': 176.0,
            'unit': 'lbs'
        }

        mock_response = Mock()
        mock_response.text = "I've prepared your weight entry."
        mock_response.function_calls = [mock_fc]

        mock_chat.send_message.return_value = mock_response

        # Mock types
        mock_types.Content.return_value = Mock()
        mock_types.Part.from_text.return_value = Mock()
        mock_types.SafetySetting.return_value = Mock()
        mock_types.GenerateContentConfig.return_value = Mock()
        mock_types.AutomaticFunctionCallingConfig.return_value = Mock()

        # Initialize service with function declarations
        service = GeminiService(api_key='test-key')
        functions = [
            {
                'name': 'create_health_metric',
                'description': 'Log weight and body metrics',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'recorded_date': {'type': 'string'},
                        'weight': {'type': 'number'}
                    }
                }
            }
        ]

        # Send message
        response, function_call = service.chat(
            "I weighed 176 lbs today",
            [],
            function_declarations=functions
        )

        # Verify function call
        assert function_call is not None
        assert function_call['name'] == 'create_health_metric'
        assert function_call['args']['weight'] == 176.0


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
