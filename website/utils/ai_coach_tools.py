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


def get_recent_health_metrics_schema() -> Dict[str, Any]:
    """
    Function schema for querying recent health metrics.

    Allows AI to READ historical health data including weight, body fat,
    measurements, and wellness indicators.
    """
    return {
        'name': 'get_recent_health_metrics',
        'description': 'Query recent health metrics including weight, body fat percentage, measurements, and wellness indicators. Use this when you need to reference the user\'s progress, trends, or current stats.',
        'parameters': {
            'type': 'object',
            'properties': {
                'days': {
                    'type': 'integer',
                    'description': 'Number of days to look back (default: 7, max: 90)',
                },
                'include_trends': {
                    'type': 'boolean',
                    'description': 'Whether to include trend calculations (weight change, averages)',
                }
            }
        }
    }


def get_workout_history_schema() -> Dict[str, Any]:
    """
    Function schema for querying recent workout sessions.

    Allows AI to READ workout history including session details and exercises.
    """
    return {
        'name': 'get_workout_history',
        'description': 'Query recent workout sessions including type, duration, exercises, and performance. Use this when discussing training progress, consistency, or planning future workouts.',
        'parameters': {
            'type': 'object',
            'properties': {
                'days': {
                    'type': 'integer',
                    'description': 'Number of days to look back (default: 7, max: 30)',
                },
                'session_type': {
                    'type': 'string',
                    'enum': ['STRENGTH', 'CARDIO', 'FLEXIBILITY', 'MARTIAL_ARTS', 'SPORTS', 'RECOVERY', 'MIXED'],
                    'description': 'Optional filter by session type'
                },
                'include_exercises': {
                    'type': 'boolean',
                    'description': 'Whether to include exercise details (sets, reps, weight)',
                }
            }
        }
    }


def get_nutrition_summary_schema() -> Dict[str, Any]:
    """
    Function schema for querying nutrition data and adherence.

    Allows AI to READ meal logs, macros, and adherence patterns.
    """
    return {
        'name': 'get_nutrition_summary',
        'description': 'Query nutrition data including meals, macros, calories, and adherence to plan. Use this when discussing diet, meal planning, or nutritional progress.',
        'parameters': {
            'type': 'object',
            'properties': {
                'days': {
                    'type': 'integer',
                    'description': 'Number of days to look back (default: 7, max: 30)',
                },
                'summary_type': {
                    'type': 'string',
                    'enum': ['daily', 'weekly'],
                    'description': 'Summarize data by day or week (default: weekly)',
                }
            }
        }
    }


def get_user_goals_schema() -> Dict[str, Any]:
    """
    Function schema for querying user goals and progress.

    Allows AI to READ active goals, targets, and progress tracking.
    """
    return {
        'name': 'get_user_goals',
        'description': 'Query user\'s fitness and health goals including targets, progress, and completion status. Use this when discussing goal setting, progress toward targets, or motivation.',
        'parameters': {
            'type': 'object',
            'properties': {
                'status': {
                    'type': 'string',
                    'enum': ['active', 'completed', 'all'],
                    'description': 'Filter by goal status (default: active)',
                }
            }
        }
    }


def get_coaching_history_schema() -> Dict[str, Any]:
    """
    Function schema for querying previous coaching sessions.

    Allows AI to READ past coaching notes, feedback, and action items.
    """
    return {
        'name': 'get_coaching_history',
        'description': 'Query previous coaching sessions including discussion notes, feedback, and action items. Use this to reference past conversations, follow up on previous advice, or check on assigned tasks.',
        'parameters': {
            'type': 'object',
            'properties': {
                'limit': {
                    'type': 'integer',
                    'description': 'Number of sessions to retrieve (default: 5, max: 20)',
                }
            }
        }
    }


def get_progress_summary_schema() -> Dict[str, Any]:
    """
    Function schema for getting comprehensive progress overview.

    Allows AI to READ aggregated metrics across all data types.
    """
    return {
        'name': 'get_progress_summary',
        'description': 'Get comprehensive progress overview including weight change, workout consistency, nutrition adherence, and goal progress. Use this for weekly check-ins or overall progress discussions.',
        'parameters': {
            'type': 'object',
            'properties': {
                'period_days': {
                    'type': 'integer',
                    'description': 'Analysis period in days (default: 30, max: 90)',
                }
            }
        }
    }


def create_behavior_definition_schema() -> Dict[str, Any]:
    """
    Function schema for creating a behavior definition.

    Allows AI to create new trackable behavior categories for the user.
    """
    return {
        'name': 'create_behavior_definition',
        'description': 'Create a new behavior definition for tracking daily habits or routines. Use this when the user wants to track a new habit, routine, or behavior. Examples: morning meditation, reading, cold shower, journaling.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'Name of the behavior (e.g., "Morning Meditation", "Read 20 Pages")'
                },
                'description': {
                    'type': 'string',
                    'description': 'Optional description or details about the behavior'
                },
                'category': {
                    'type': 'string',
                    'enum': ['HEALTH', 'FITNESS', 'NUTRITION', 'LEARNING', 'PRODUCTIVITY', 'WELLNESS', 'CUSTOM'],
                    'description': 'Category of the behavior',
                },
                'icon': {
                    'type': 'string',
                    'description': 'Bootstrap icon class (e.g., "bi-book", "bi-heart", "bi-lightning"). See https://icons.getbootstrap.com/',
                },
                'color': {
                    'type': 'string',
                    'description': 'Hex color code for the behavior (e.g., "#4A90E2", "#E27D60")',
                },
                'target_frequency': {
                    'type': 'integer',
                    'description': 'Target number of days per week to complete this behavior (1-7)',
                }
            },
            'required': ['name']
        }
    }


def log_behavior_schema() -> Dict[str, Any]:
    """
    Function schema for logging behavior completion.

    Allows AI to mark behaviors as completed for a specific date.
    """
    return {
        'name': 'log_behavior',
        'description': 'Log completion of a behavior for a specific date. Use this when the user mentions they completed a tracked behavior or wants to mark something as done.',
        'parameters': {
            'type': 'object',
            'properties': {
                'behavior_name': {
                    'type': 'string',
                    'description': 'Name of the behavior to log (must match an existing behavior definition)'
                },
                'tracked_date': {
                    'type': 'string',
                    'description': 'Date of completion in ISO format (YYYY-MM-DD). Use today\'s date if not specified.'
                },
                'completed': {
                    'type': 'boolean',
                    'description': 'Whether the behavior was completed (true) or not (false)',
                },
                'notes': {
                    'type': 'string',
                    'description': 'Optional notes about the behavior completion'
                }
            },
            'required': ['behavior_name', 'tracked_date']
        }
    }


def get_behavior_tracking_schema() -> Dict[str, Any]:
    """
    Function schema for querying behavior tracking data.

    Allows AI to READ behavior completion history, streaks, and patterns.
    """
    return {
        'name': 'get_behavior_tracking',
        'description': 'Query behavior tracking data including completion history, current streaks, and adherence patterns. Use this when discussing habits, consistency, or progress on tracked behaviors.',
        'parameters': {
            'type': 'object',
            'properties': {
                'days': {
                    'type': 'integer',
                    'description': 'Number of days to look back (default: 7, max: 30)',
                },
                'behavior_name': {
                    'type': 'string',
                    'description': 'Optional filter for a specific behavior by name. If omitted, returns data for all behaviors.'
                }
            }
        }
    }


def get_behavior_plan_compliance_schema() -> Dict[str, Any]:
    """
    Function schema for querying behavior plan compliance.

    Allows AI to READ adherence to target frequencies and identify gaps.
    """
    return {
        'name': 'get_behavior_plan_compliance',
        'description': 'Analyze behavior plan compliance by comparing actual completion frequency against target frequency. Use this when checking if the user is staying on track with their habits or when they ask about their consistency.',
        'parameters': {
            'type': 'object',
            'properties': {
                'period': {
                    'type': 'string',
                    'enum': ['week', 'month'],
                    'description': 'Analysis period (default: week)',
                },
                'include_recommendations': {
                    'type': 'boolean',
                    'description': 'Whether to include AI-generated recommendations for improvement',
                }
            }
        }
    }


def create_batch_records_schema() -> Dict[str, Any]:
    """
    Function schema for creating multiple records at once.

    Allows the AI to create workout, meal, health metric, and other records
    in a single function call when the user mentions multiple items.
    """
    return {
        'name': 'create_batch_records',
        'description': 'Create multiple records at once (workouts, meals, health metrics, etc.) in a single operation. Use this when the user mentions multiple things to log in one message, such as "I did a workout and ate breakfast" or "I weighed myself and logged my meals today".',
        'parameters': {
            'type': 'object',
            'properties': {
                'records': {
                    'type': 'array',
                    'description': 'Array of records to create. Each record specifies its type and data.',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'record_type': {
                                'type': 'string',
                                'enum': ['health_metric', 'meal_log', 'workout', 'coaching_session', 'behavior_definition', 'behavior_log'],
                                'description': 'Type of record to create'
                            },
                            'data': {
                                'type': 'object',
                                'description': 'Record data. Structure should match the schema for the specified record_type. For health_metric: include recorded_date, weight_lbs, body_fat_percentage, etc. For meal_log: include meal_date, meal_type, calories, protein_g, etc. For workout: include session_date, session_type, duration_minutes, exercises array. For coaching_session: include session_date, discussion_notes, coach_feedback. For behavior_definition: include name, category, description. For behavior_log: include tracked_date, behavior_name, completed.'
                            }
                        },
                        'required': ['record_type', 'data']
                    }
                }
            },
            'required': ['records']
        }
    }


def get_all_function_declarations() -> List[Dict[str, Any]]:
    """
    Get all function declarations for Gemini function calling.

    Returns:
        List of function schema dictionaries
    """
    return [
        # WRITE operations (create records)
        create_batch_records_schema(),  # NEW: Batch creation (highest priority)
        create_health_metric_schema(),
        create_meal_log_schema(),
        create_workout_schema(),
        create_coaching_session_schema(),
        create_behavior_definition_schema(),
        log_behavior_schema(),
        # READ operations (query data)
        get_recent_health_metrics_schema(),
        get_workout_history_schema(),
        get_nutrition_summary_schema(),
        get_user_goals_schema(),
        get_coaching_history_schema(),
        get_progress_summary_schema(),
        get_behavior_tracking_schema(),
        get_behavior_plan_compliance_schema()
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
        # WRITE operations
        'create_health_metric': create_health_metric_schema(),
        'create_meal_log': create_meal_log_schema(),
        'create_workout': create_workout_schema(),
        'create_coaching_session': create_coaching_session_schema(),
        'create_behavior_definition': create_behavior_definition_schema(),
        'log_behavior': log_behavior_schema(),
        # READ operations
        'get_recent_health_metrics': get_recent_health_metrics_schema(),
        'get_workout_history': get_workout_history_schema(),
        'get_nutrition_summary': get_nutrition_summary_schema(),
        'get_user_goals': get_user_goals_schema(),
        'get_coaching_history': get_coaching_history_schema(),
        'get_progress_summary': get_progress_summary_schema(),
        'get_behavior_tracking': get_behavior_tracking_schema(),
        'get_behavior_plan_compliance': get_behavior_plan_compliance_schema()
    }

    if function_name not in schemas:
        raise ValueError(f"Unknown function: {function_name}")

    return schemas[function_name]
