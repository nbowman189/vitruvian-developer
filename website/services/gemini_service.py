"""
Gemini Service
==============

Google Gemini AI integration service for AI coaching interface.
Handles conversation management, function calling, and persona loading.
"""

import os
import logging
from typing import List, Dict, Tuple, Optional, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)


# The Transformative Trainer Persona
TRANSFORMATIVE_TRAINER_PERSONA = """You are an expert personal trainer with 20 years of experience, specializing in guiding clients from morbid obesity to a state of health, fitness, and strength. Your expertise lies in a holistic approach, focusing on sustainable nutrition, practical meal planning, effective bodyweight strength training, and functional fitness. Your communication style is that of a tough love drill sergeant, pushing clients to achieve their best, but you are also deeply encouraging and empathetic when they face struggles. You operate on the core principles that sustainable lifestyle changes, a strong mindset, and unwavering consistency are paramount, far outweighing short bursts of intensity. Your primary target audience is individuals seeking a holistic approach to health who have struggled with long-term weight loss.

As an AI coach, when users mention health metrics, workouts, meals, or coaching discussions, you will suggest structured database records to help them track their progress. You have access to 4 function tools:

1. **create_health_metric**: For weight, body fat, measurements, and wellness tracking
2. **create_meal_log**: For meal and nutrition tracking
3. **create_workout**: For workout sessions with exercises
4. **create_coaching_session**: For coaching notes and feedback

When appropriate, use these functions to suggest records. The user will review and approve before saving to their database. Always be conversational first, then suggest the record as a helpful tracking tool."""


class GeminiService:
    """
    Google Gemini AI service for conversational health coaching.

    Handles:
    - Persona-based AI conversations
    - Function calling for database record suggestions
    - Context management and pruning
    - Error handling and safety settings
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini service with API key.

        Args:
            api_key: Google Gemini API key (defaults to GEMINI_API_KEY env var)

        Raises:
            ValueError: If API key is not provided or found in environment
        """
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it in your environment or pass it to GeminiService."
            )

        # Configure the Gemini API
        genai.configure(api_key=self.api_key)

        # Initialize the model with safety settings
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-pro',
            generation_config={
                'temperature': 0.7,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 2048,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )

        self.system_prompt = TRANSFORMATIVE_TRAINER_PERSONA
        logger.info("GeminiService initialized successfully")

    def chat(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        function_declarations: Optional[List[Dict]] = None,
        max_context_messages: int = 10
    ) -> Tuple[str, Optional[Dict]]:
        """
        Send a message to Gemini AI and get response.

        Args:
            user_message: The user's message
            conversation_history: List of previous messages with 'role' and 'content' keys
            function_declarations: List of function schemas for function calling
            max_context_messages: Maximum number of previous messages to include (default: 10)

        Returns:
            Tuple of (assistant_response, function_call_data)
            - assistant_response: The AI's text response
            - function_call_data: Dict with function call details if AI wants to call a function, else None

        Raises:
            Exception: If Gemini API call fails
        """
        try:
            # Prune conversation history to last N messages
            recent_history = conversation_history[-max_context_messages:] if conversation_history else []

            # Build the full conversation context
            messages = []

            # Add system prompt as first message
            messages.append({
                'role': 'user',
                'parts': [self.system_prompt]
            })
            messages.append({
                'role': 'model',
                'parts': ["I understand. I am The Transformative Trainer, ready to help you on your health and fitness journey with tough love, empathy, and structured tracking tools. Let's get started!"]
            })

            # Add conversation history
            for msg in recent_history:
                role = 'model' if msg['role'] == 'assistant' else 'user'
                messages.append({
                    'role': role,
                    'parts': [msg['content']]
                })

            # Add current user message
            messages.append({
                'role': 'user',
                'parts': [user_message]
            })

            # Configure function calling if provided
            tools = None
            if function_declarations:
                tools = [{'function_declarations': function_declarations}]

            # Start chat session
            chat = self.model.start_chat(history=messages[:-1])

            # Send message with optional function calling
            if tools:
                response = chat.send_message(
                    user_message,
                    tools=tools
                )
            else:
                response = chat.send_message(user_message)

            # Extract response
            assistant_response = ""
            function_call = None

            # Check if there's a function call
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]

                if candidate.content.parts:
                    for part in candidate.content.parts:
                        # Check for text response
                        if hasattr(part, 'text') and part.text:
                            assistant_response += part.text

                        # Check for function call
                        if hasattr(part, 'function_call') and part.function_call:
                            fc = part.function_call
                            function_call = {
                                'name': fc.name,
                                'args': dict(fc.args) if fc.args else {}
                            }
                            logger.info(f"Function call detected: {fc.name}")

            # If no text response but there's a function call, add a default message
            if not assistant_response and function_call:
                assistant_response = self._get_default_function_call_message(function_call['name'])

            logger.info(f"Gemini response received. Function call: {function_call is not None}")
            return assistant_response, function_call

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get response from AI coach: {str(e)}")

    def _get_default_function_call_message(self, function_name: str) -> str:
        """
        Get a default message when a function call is made without accompanying text.

        Args:
            function_name: Name of the function being called

        Returns:
            Default message string
        """
        messages = {
            'create_health_metric': "Great! I've prepared a health metric record for you. Review and save it when you're ready.",
            'create_meal_log': "Excellent! I've created a meal log entry. Please review the details and save it.",
            'create_workout': "Nice work! I've logged your workout session. Check the details and save it to your history.",
            'create_coaching_session': "I've captured our coaching discussion. Review the notes and save them for your records."
        }
        return messages.get(function_name, "I've prepared a record for you to review and save.")

    def _build_conversation_context(
        self,
        conversation_history: List[Dict[str, str]],
        max_messages: int
    ) -> str:
        """
        Build conversation context string from history.

        Args:
            conversation_history: List of messages
            max_messages: Maximum number of messages to include

        Returns:
            Formatted conversation context string
        """
        recent_history = conversation_history[-max_messages:] if conversation_history else []

        context_lines = []
        for msg in recent_history:
            role_label = "User" if msg['role'] == 'user' else "Coach"
            context_lines.append(f"{role_label}: {msg['content']}")

        return "\n".join(context_lines)

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """
        Validate Gemini API key by making a test call.

        Args:
            api_key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-pro')
            model.generate_content("Test")
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False

    @property
    def is_configured(self) -> bool:
        """Check if service is properly configured."""
        return bool(self.api_key)
