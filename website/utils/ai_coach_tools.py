"""
AI Coach Function Tools
========================

Function declarations (schemas) for Gemini function calling.
These define the structure of database records that the AI can suggest creating.
"""

from typing import List, Dict, Any


def create_health_metric_schema() -> Dict[str, Any]:
    """
    Function schema for creating a health metric record.

    Captures:
    - Date
    - Weight and body composition
    - Body measurements
    - Wellness indicators
    - Notes
    """
    return {
        'name': 'create_health_metric',
        'description': 'Create a health metric record to track weight, body fat, measurements, and wellness indicators. Use this when the user mentions their weight, body measurements, or how they\'re feeling physically.',
        'parameters': {
            'type': 'object',
            'properties': {
                'recorded_date': {
                    'type': 'string',
                    'description': 'Date of the measurement in ISO format (YYYY-MM-DD). Use today\'s date if not specified.'
                },
                'weight_lbs': {
                    'type': 'number',
                    'description': 'Weight in pounds'
                },
                'body_fat_percentage': {
                    'type': 'number',
                    'description': 'Body fat percentage (0-100)'
                },
                'waist_inches': {
                    'type': 'number',
                    'description': 'Waist measurement in inches'
                },
                'chest_inches': {
                    'type': 'number',
                    'description': 'Chest measurement in inches'
                },
                'energy_level': {
                    'type': 'integer',
                    'description': 'Energy level on a scale of 1-10'
                },
                'mood': {
                    'type': 'integer',
                    'description': 'Mood on a scale of 1-10'
                },
                'sleep_quality': {
                    'type': 'integer',
                    'description': 'Sleep quality on a scale of 1-10'
                },
                'notes': {
                    'type': 'string',
                    'description': 'Additional notes or observations'
                }
            },
            'required': ['recorded_date']
        }
    }


def create_meal_log_schema() -> Dict[str, Any]:
    """
    Function schema for creating a meal log record.

    Captures:
    - Date and meal type
    - Calories and macronutrients
    - Description of food
    """
    return {
        'name': 'create_meal_log',
        'description': 'Create a meal log entry to track nutrition. Use this when the user mentions what they ate, their calories, or macros.',
        'parameters': {
            'type': 'object',
            'properties': {
                'meal_date': {
                    'type': 'string',
                    'description': 'Date of the meal in ISO format (YYYY-MM-DD). Use today\'s date if not specified.'
                },
                'meal_type': {
                    'type': 'string',
                    'enum': ['BREAKFAST', 'LUNCH', 'DINNER', 'SNACK', 'PRE_WORKOUT', 'POST_WORKOUT', 'OTHER'],
                    'description': 'Type of meal'
                },
                'calories': {
                    'type': 'integer',
                    'description': 'Total calories consumed'
                },
                'protein_g': {
                    'type': 'number',
                    'description': 'Protein in grams'
                },
                'carbs_g': {
                    'type': 'number',
                    'description': 'Carbohydrates in grams'
                },
                'fat_g': {
                    'type': 'number',
                    'description': 'Fat in grams'
                },
                'fiber_g': {
                    'type': 'number',
                    'description': 'Fiber in grams'
                },
                'description': {
                    'type': 'string',
                    'description': 'Description of the meal or food items'
                }
            },
            'required': ['meal_date', 'meal_type']
        }
    }


def create_workout_schema() -> Dict[str, Any]:
    """
    Function schema for creating a workout session with exercises.

    Captures:
    - Session date and type
    - Duration
    - List of exercises with sets, reps, weight
    - Notes
    """
    return {
        'name': 'create_workout',
        'description': 'Create a workout session record with exercises. Use this when the user mentions their workout, exercises performed, or training session.',
        'parameters': {
            'type': 'object',
            'properties': {
                'session_date': {
                    'type': 'string',
                    'description': 'Date of the workout in ISO format (YYYY-MM-DD). Use today\'s date if not specified.'
                },
                'session_type': {
                    'type': 'string',
                    'enum': ['STRENGTH', 'CARDIO', 'FLEXIBILITY', 'MARTIAL_ARTS', 'SPORTS', 'RECOVERY', 'MIXED'],
                    'description': 'Type of workout session'
                },
                'duration_minutes': {
                    'type': 'integer',
                    'description': 'Duration of workout in minutes'
                },
                'exercises': {
                    'type': 'array',
                    'description': 'List of exercises performed',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'exercise_name': {
                                'type': 'string',
                                'description': 'Name of the exercise'
                            },
                            'sets': {
                                'type': 'integer',
                                'description': 'Number of sets performed'
                            },
                            'reps': {
                                'type': 'integer',
                                'description': 'Number of repetitions per set'
                            },
                            'weight_lbs': {
                                'type': 'number',
                                'description': 'Weight used in pounds (if applicable)'
                            },
                            'duration_seconds': {
                                'type': 'integer',
                                'description': 'Duration in seconds (for timed exercises)'
                            },
                            'notes': {
                                'type': 'string',
                                'description': 'Notes about the exercise performance'
                            }
                        },
                        'required': ['exercise_name']
                    }
                },
                'intensity_level': {
                    'type': 'integer',
                    'description': 'Perceived exertion level (1-10)'
                },
                'notes': {
                    'type': 'string',
                    'description': 'General notes about the workout session'
                }
            },
            'required': ['session_date', 'session_type']
        }
    }


def create_coaching_session_schema() -> Dict[str, Any]:
    """
    Function schema for creating a coaching session record.

    Captures:
    - Session date
    - Discussion notes
    - Coach feedback
    - Action items
    """
    return {
        'name': 'create_coaching_session',
        'description': 'Create a coaching session record to capture our discussion, feedback, and action items. Use this when wrapping up a coaching conversation or when the user wants to save our discussion.',
        'parameters': {
            'type': 'object',
            'properties': {
                'session_date': {
                    'type': 'string',
                    'description': 'Date of the coaching session in ISO format (YYYY-MM-DD). Use today\'s date if not specified.'
                },
                'discussion_notes': {
                    'type': 'string',
                    'description': 'Summary of topics discussed during the session'
                },
                'coach_feedback': {
                    'type': 'string',
                    'description': 'Coach\'s feedback, observations, and recommendations'
                },
                'action_items': {
                    'type': 'array',
                    'description': 'List of action items or tasks for the client',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': ['session_date']
        }
    }


def get_all_function_declarations() -> List[Dict[str, Any]]:
    """
    Get all function declarations for Gemini function calling.

    Returns:
        List of function schema dictionaries
    """
    return [
        create_health_metric_schema(),
        create_meal_log_schema(),
        create_workout_schema(),
        create_coaching_session_schema()
    ]


def get_function_schema_by_name(function_name: str) -> Dict[str, Any]:
    """
    Get a specific function schema by name.

    Args:
        function_name: Name of the function

    Returns:
        Function schema dictionary

    Raises:
        ValueError: If function name is not found
    """
    schemas = {
        'create_health_metric': create_health_metric_schema(),
        'create_meal_log': create_meal_log_schema(),
        'create_workout': create_workout_schema(),
        'create_coaching_session': create_coaching_session_schema()
    }

    if function_name not in schemas:
        raise ValueError(f"Unknown function: {function_name}")

    return schemas[function_name]
