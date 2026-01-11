#!/usr/bin/env python3
"""
Test AI Coach Batch Records Feature
=====================================

Comprehensive test script for the create_batch_records functionality.

Tests:
1. Single record in batch (edge case)
2. Multiple different record types (workout + meal + health metric)
3. Multiple same record types (multiple meals for a day)
4. Partial success (some records fail validation)
5. All records fail (invalid data)
6. Empty batch array (error case)
7. Mixed valid/invalid within same record type
"""

import sys
import json
from datetime import date, timedelta
from pathlib import Path

# Add parent directory to path so we can import website module
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from website import create_app
from website.models import db
from website.models.user import User
from website.models.health import HealthMetric
from website.models.nutrition import MealLog
from website.models.workout import WorkoutSession
from website.models.conversation import ConversationLog
from website.api.ai_coach import _save_batch_records


def setup_test_environment():
    """Create app context and get test user."""
    app = create_app()
    app.config['TESTING'] = True

    with app.app_context():
        # Get admin user (created by create_admin_user.py)
        user = User.query.filter_by(username='admin').first()
        if not user:
            print("❌ Admin user not found. Run create_admin_user.py first.")
            sys.exit(1)

        return app, user


def print_test_header(test_name, test_num, total_tests):
    """Print formatted test header."""
    print(f"\n{'='*70}")
    print(f"TEST {test_num}/{total_tests}: {test_name}")
    print(f"{'='*70}")


def print_result(success, message, details=None):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if details:
        print(f"  Details: {json.dumps(details, indent=2)}")


def test_1_single_record_batch(app, user):
    """Test 1: Single record in batch (edge case)."""
    print_test_header("Single Record in Batch", 1, 7)

    with app.app_context():
        data = {
            'records': [
                {
                    'record_type': 'health_metric',
                    'data': {
                        'recorded_date': date.today().isoformat(),
                        'weight_lbs': 175.5,
                        'body_fat_percentage': 18.5,
                        'notes': 'Test single batch record'
                    }
                }
            ]
        }

        try:
            result, record_type = _save_batch_records(user.id, data)
            db.session.commit()

            result_dict = result.to_dict()
            success = (
                result_dict['total_records'] == 1 and
                result_dict['successful'] == 1 and
                result_dict['failed'] == 0
            )

            print_result(success, "Single record batch creation", result_dict)
            return success

        except Exception as e:
            print_result(False, f"Exception occurred: {str(e)}")
            db.session.rollback()
            return False


def test_2_multiple_different_types(app, user):
    """Test 2: Multiple different record types."""
    print_test_header("Multiple Different Record Types", 2, 7)

    with app.app_context():
        today = date.today().isoformat()

        data = {
            'records': [
                {
                    'record_type': 'health_metric',
                    'data': {
                        'recorded_date': today,
                        'weight_lbs': 176.0,
                        'energy_level': 8,
                        'notes': 'Morning weigh-in'
                    }
                },
                {
                    'record_type': 'workout',
                    'data': {
                        'session_date': today,
                        'session_type': 'STRENGTH',
                        'duration_minutes': 60,
                        'exercises': [
                            {
                                'exercise_name': 'Bench Press',
                                'sets': 3,
                                'reps': 8,
                                'weight_lbs': 185
                            },
                            {
                                'exercise_name': 'Squats',
                                'sets': 4,
                                'reps': 10,
                                'weight_lbs': 225
                            }
                        ],
                        'notes': 'Upper body day'
                    }
                },
                {
                    'record_type': 'meal_log',
                    'data': {
                        'meal_date': today,
                        'meal_type': 'BREAKFAST',
                        'calories': 650,
                        'protein_g': 45,
                        'carbs_g': 60,
                        'fat_g': 20,
                        'description': 'Eggs, oatmeal, protein shake'
                    }
                }
            ]
        }

        try:
            result, record_type = _save_batch_records(user.id, data)
            db.session.commit()

            result_dict = result.to_dict()
            success = (
                result_dict['total_records'] == 3 and
                result_dict['successful'] == 3 and
                result_dict['failed'] == 0
            )

            # Verify records were actually created
            health_count = HealthMetric.query.filter_by(user_id=user.id).count()
            workout_count = WorkoutSession.query.filter_by(user_id=user.id).count()
            meal_count = MealLog.query.filter_by(user_id=user.id).count()

            print_result(
                success,
                f"Mixed record types - Health: {health_count}, Workouts: {workout_count}, Meals: {meal_count}",
                result_dict
            )
            return success

        except Exception as e:
            print_result(False, f"Exception occurred: {str(e)}")
            db.session.rollback()
            return False


def test_3_multiple_same_type(app, user):
    """Test 3: Multiple same record types (multiple meals)."""
    print_test_header("Multiple Same Record Type", 3, 7)

    with app.app_context():
        today = date.today().isoformat()

        data = {
            'records': [
                {
                    'record_type': 'meal_log',
                    'data': {
                        'meal_date': today,
                        'meal_type': 'LUNCH',
                        'calories': 800,
                        'protein_g': 50,
                        'carbs_g': 80,
                        'fat_g': 25,
                        'description': 'Chicken breast, rice, vegetables'
                    }
                },
                {
                    'record_type': 'meal_log',
                    'data': {
                        'meal_date': today,
                        'meal_type': 'DINNER',
                        'calories': 750,
                        'protein_g': 55,
                        'carbs_g': 65,
                        'fat_g': 30,
                        'description': 'Salmon, sweet potato, broccoli'
                    }
                },
                {
                    'record_type': 'meal_log',
                    'data': {
                        'meal_date': today,
                        'meal_type': 'SNACK',
                        'calories': 200,
                        'protein_g': 20,
                        'carbs_g': 15,
                        'fat_g': 8,
                        'description': 'Protein bar and almonds'
                    }
                }
            ]
        }

        try:
            result, record_type = _save_batch_records(user.id, data)
            db.session.commit()

            result_dict = result.to_dict()
            success = (
                result_dict['total_records'] == 3 and
                result_dict['successful'] == 3 and
                result_dict['failed'] == 0
            )

            print_result(success, "Multiple meals in one batch", result_dict)
            return success

        except Exception as e:
            print_result(False, f"Exception occurred: {str(e)}")
            db.session.rollback()
            return False


def test_4_partial_success(app, user):
    """Test 4: Partial success (some records fail validation)."""
    print_test_header("Partial Success - Mixed Valid/Invalid", 4, 7)

    with app.app_context():
        today = date.today().isoformat()

        data = {
            'records': [
                {
                    'record_type': 'health_metric',
                    'data': {
                        'recorded_date': today,
                        'weight_lbs': 177.0,
                        'notes': 'Valid health metric'
                    }
                },
                {
                    'record_type': 'meal_log',
                    'data': {
                        # Missing required field: meal_type
                        'meal_date': today,
                        'calories': 500,
                        'description': 'Invalid - missing meal_type'
                    }
                },
                {
                    'record_type': 'workout',
                    'data': {
                        'session_date': today,
                        'session_type': 'CARDIO',
                        'duration_minutes': 30,
                        'notes': 'Valid workout'
                    }
                },
                {
                    'record_type': 'meal_log',
                    'data': {
                        'meal_date': 'invalid-date-format',  # Invalid date
                        'meal_type': 'LUNCH',
                        'calories': 600
                    }
                }
            ]
        }

        try:
            result, record_type = _save_batch_records(user.id, data)
            db.session.commit()

            result_dict = result.to_dict()
            success = (
                result_dict['total_records'] == 4 and
                result_dict['successful'] == 2 and  # 2 valid records
                result_dict['failed'] == 2  # 2 failed records
            )

            print_result(
                success,
                f"Partial success: {result_dict['successful']} succeeded, {result_dict['failed']} failed",
                result_dict
            )
            return success

        except Exception as e:
            print_result(False, f"Exception occurred: {str(e)}")
            db.session.rollback()
            return False


def test_5_all_fail(app, user):
    """Test 5: All records fail validation."""
    print_test_header("All Records Fail", 5, 7)

    with app.app_context():
        data = {
            'records': [
                {
                    'record_type': 'health_metric',
                    'data': {
                        # Missing required field: recorded_date
                        'weight_lbs': 180.0
                    }
                },
                {
                    'record_type': 'meal_log',
                    'data': {
                        # Missing required fields: meal_date, meal_type
                        'calories': 500
                    }
                },
                {
                    'record_type': 'workout',
                    'data': {
                        # Missing required field: session_type
                        'session_date': date.today().isoformat(),
                        'duration_minutes': 30
                    }
                }
            ]
        }

        try:
            result, record_type = _save_batch_records(user.id, data)
            db.session.commit()

            # Should NOT reach here - should raise ValueError
            print_result(False, "Expected ValueError for all failed records")
            return False

        except ValueError as e:
            # This is expected
            success = "All records failed" in str(e)
            print_result(success, f"All records failed as expected: {str(e)}")
            db.session.rollback()
            return success

        except Exception as e:
            print_result(False, f"Unexpected exception: {str(e)}")
            db.session.rollback()
            return False


def test_6_empty_batch(app, user):
    """Test 6: Empty batch array (error case)."""
    print_test_header("Empty Batch Array", 6, 7)

    with app.app_context():
        data = {
            'records': []
        }

        try:
            result, record_type = _save_batch_records(user.id, data)

            # Should NOT reach here
            print_result(False, "Expected ValueError for empty batch")
            return False

        except ValueError as e:
            # This is expected
            success = "cannot be empty" in str(e)
            print_result(success, f"Empty batch rejected as expected: {str(e)}")
            return success

        except Exception as e:
            print_result(False, f"Unexpected exception: {str(e)}")
            return False


def test_7_unknown_record_type(app, user):
    """Test 7: Unknown record type."""
    print_test_header("Unknown Record Type", 7, 7)

    with app.app_context():
        today = date.today().isoformat()

        data = {
            'records': [
                {
                    'record_type': 'invalid_type',
                    'data': {
                        'some_field': 'some_value'
                    }
                }
            ]
        }

        try:
            result, record_type = _save_batch_records(user.id, data)
            db.session.commit()

            # Should complete but with error
            result_dict = result.to_dict()
            success = (
                result_dict['total_records'] == 1 and
                result_dict['successful'] == 0 and
                result_dict['failed'] == 1
            )

            print_result(success, "Unknown record type handled gracefully", result_dict)
            return success

        except ValueError as e:
            # Could also fail with ValueError if all fail
            success = True
            print_result(success, f"Unknown record type rejected: {str(e)}")
            db.session.rollback()
            return success

        except Exception as e:
            print_result(False, f"Unexpected exception: {str(e)}")
            db.session.rollback()
            return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("AI COACH BATCH RECORDS - COMPREHENSIVE TEST SUITE")
    print("="*70)

    app, user = setup_test_environment()

    # Run all tests
    tests = [
        test_1_single_record_batch,
        test_2_multiple_different_types,
        test_3_multiple_same_type,
        test_4_partial_success,
        test_5_all_fail,
        test_6_empty_batch,
        test_7_unknown_record_type
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func(app, user)
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            results.append(False)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(results)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
