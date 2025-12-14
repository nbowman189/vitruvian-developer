"""
Data Validation Utilities
==========================

Provides validation functions for all data types before database insertion.
Ensures data integrity and prevents invalid data from entering the database.
"""

from datetime import datetime, date
from typing import Optional, Tuple, Any
import re


class ValidationResult:
    """Container for validation results"""

    def __init__(self, is_valid: bool, value: Any = None, error: str = None):
        self.is_valid = is_valid
        self.value = value
        self.error = error

    def __bool__(self):
        return self.is_valid

    def __repr__(self):
        if self.is_valid:
            return f"<Valid: {self.value}>"
        return f"<Invalid: {self.error}>"


def validate_date(date_str: str, field_name: str = "date") -> ValidationResult:
    """
    Validate and parse date string in YYYY-MM-DD format.

    Args:
        date_str: Date string to validate
        field_name: Name of field for error messages

    Returns:
        ValidationResult with parsed date object or error message
    """
    if not date_str or date_str in ['', 'None', 'N/A', 'null']:
        return ValidationResult(False, None, f"{field_name} is missing or invalid")

    try:
        # Try parsing as YYYY-MM-DD
        parsed_date = datetime.strptime(str(date_str).strip(), '%Y-%m-%d').date()

        # Sanity check: date should be reasonable (1900-2100)
        if parsed_date.year < 1900 or parsed_date.year > 2100:
            return ValidationResult(False, None, f"{field_name} year is out of reasonable range: {parsed_date.year}")

        return ValidationResult(True, parsed_date, None)

    except ValueError as e:
        return ValidationResult(False, None, f"{field_name} has invalid format (expected YYYY-MM-DD): {date_str}")


def validate_float(value: Any, field_name: str, min_val: Optional[float] = None,
                   max_val: Optional[float] = None, allow_none: bool = True) -> ValidationResult:
    """
    Validate and parse float value with optional range checking.

    Args:
        value: Value to validate
        field_name: Name of field for error messages
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        allow_none: Whether None/empty values are acceptable

    Returns:
        ValidationResult with parsed float or error message
    """
    # Handle None/empty cases
    if value is None or str(value).strip() in ['', 'None', 'N/A', 'null']:
        if allow_none:
            return ValidationResult(True, None, None)
        return ValidationResult(False, None, f"{field_name} is required but missing")

    try:
        float_val = float(str(value).strip())

        # Range validation
        if min_val is not None and float_val < min_val:
            return ValidationResult(False, None, f"{field_name} ({float_val}) is below minimum ({min_val})")

        if max_val is not None and float_val > max_val:
            return ValidationResult(False, None, f"{field_name} ({float_val}) is above maximum ({max_val})")

        return ValidationResult(True, float_val, None)

    except ValueError:
        return ValidationResult(False, None, f"{field_name} is not a valid number: {value}")


def validate_int(value: Any, field_name: str, min_val: Optional[int] = None,
                 max_val: Optional[int] = None, allow_none: bool = True) -> ValidationResult:
    """
    Validate and parse integer value with optional range checking.

    Args:
        value: Value to validate
        field_name: Name of field for error messages
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        allow_none: Whether None/empty values are acceptable

    Returns:
        ValidationResult with parsed int or error message
    """
    # Handle None/empty cases
    if value is None or str(value).strip() in ['', 'None', 'N/A', 'null']:
        if allow_none:
            return ValidationResult(True, None, None)
        return ValidationResult(False, None, f"{field_name} is required but missing")

    try:
        int_val = int(float(str(value).strip()))  # float() first to handle "10.0" strings

        # Range validation
        if min_val is not None and int_val < min_val:
            return ValidationResult(False, None, f"{field_name} ({int_val}) is below minimum ({min_val})")

        if max_val is not None and int_val > max_val:
            return ValidationResult(False, None, f"{field_name} ({int_val}) is above maximum ({max_val})")

        return ValidationResult(True, int_val, None)

    except ValueError:
        return ValidationResult(False, None, f"{field_name} is not a valid integer: {value}")


def validate_text(value: Any, field_name: str, max_length: Optional[int] = None,
                  allow_empty: bool = True) -> ValidationResult:
    """
    Validate and sanitize text value.

    Args:
        value: Value to validate
        field_name: Name of field for error messages
        max_length: Maximum allowed length
        allow_empty: Whether empty strings are acceptable

    Returns:
        ValidationResult with sanitized text or error message
    """
    if value is None or str(value).strip() == '':
        if allow_empty:
            return ValidationResult(True, None, None)
        return ValidationResult(False, None, f"{field_name} is required but missing")

    text = str(value).strip()

    if max_length is not None and len(text) > max_length:
        return ValidationResult(False, None,
                              f"{field_name} exceeds maximum length ({len(text)} > {max_length})")

    return ValidationResult(True, text, None)


def validate_weight(weight: Any) -> ValidationResult:
    """Validate weight in pounds (must be positive, reasonable range)"""
    return validate_float(weight, "weight", min_val=50.0, max_val=1000.0, allow_none=True)


def validate_body_fat(body_fat: Any) -> ValidationResult:
    """Validate body fat percentage (0-100%)"""
    return validate_float(body_fat, "body_fat_percentage", min_val=0.0, max_val=100.0, allow_none=True)


def validate_calories(calories: Any) -> ValidationResult:
    """Validate calorie count (must be positive, reasonable range)"""
    return validate_int(calories, "calories", min_val=0, max_val=10000, allow_none=True)


def validate_sets_reps(value: Any, field_name: str) -> ValidationResult:
    """Validate sets or reps count"""
    return validate_int(value, field_name, min_val=1, max_val=500, allow_none=True)


def validate_duration(minutes: Any, field_name: str = "duration") -> ValidationResult:
    """Validate duration in minutes"""
    return validate_int(minutes, field_name, min_val=1, max_val=480, allow_none=True)


def validate_scale_rating(rating: Any, field_name: str) -> ValidationResult:
    """Validate 1-10 scale rating"""
    return validate_int(rating, field_name, min_val=1, max_val=10, allow_none=True)


def sanitize_notes(notes: str) -> str:
    """
    Sanitize notes text by stripping whitespace and normalizing.

    Args:
        notes: Raw notes text

    Returns:
        Sanitized notes text or None
    """
    if not notes or str(notes).strip() in ['', 'None', 'N/A', 'null']:
        return None

    return str(notes).strip()


def parse_sets_reps_notation(notation: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse sets x reps notation like "3 sets of 10 reps" or "3x10" or "3 sets: 10, 12, 15 reps".

    Args:
        notation: String containing sets and reps information

    Returns:
        Tuple of (sets, average_reps) or (None, None) if unparseable
    """
    if not notation:
        return None, None

    notation = str(notation).strip().lower()

    # Pattern 1: "3x10" or "3 x 10"
    pattern1 = r'(\d+)\s*x\s*(\d+)'
    match = re.search(pattern1, notation)
    if match:
        sets = int(match.group(1))
        reps = int(match.group(2))
        return sets, reps

    # Pattern 2: "3 sets of 10 reps"
    pattern2 = r'(\d+)\s*sets?\s*of\s*(\d+)\s*reps?'
    match = re.search(pattern2, notation)
    if match:
        sets = int(match.group(1))
        reps = int(match.group(2))
        return sets, reps

    # Pattern 3: "3 sets: 10, 12, 15 reps" - extract sets and calculate average
    pattern3 = r'(\d+)\s*sets?[:]\s*([\d,\s]+)\s*reps?'
    match = re.search(pattern3, notation)
    if match:
        sets = int(match.group(1))
        reps_str = match.group(2)
        reps_list = [int(r.strip()) for r in reps_str.split(',') if r.strip().isdigit()]
        if reps_list:
            avg_reps = int(sum(reps_list) / len(reps_list))
            return sets, avg_reps

    return None, None


def validate_health_metric_row(row: dict) -> Tuple[bool, dict, list]:
    """
    Validate a complete health metric row.

    Args:
        row: Dictionary with keys like 'date', 'weight', 'body_fat', 'notes'

    Returns:
        Tuple of (is_valid, validated_data, errors)
    """
    errors = []
    validated = {}

    # Validate date (required)
    date_result = validate_date(row.get('date', ''), 'date')
    if date_result:
        validated['recorded_date'] = date_result.value
    else:
        errors.append(date_result.error)
        return False, {}, errors

    # Validate weight (optional)
    weight_result = validate_weight(row.get('weight'))
    if weight_result:
        validated['weight_lbs'] = weight_result.value
    else:
        errors.append(weight_result.error)

    # Validate body fat (optional)
    bf_result = validate_body_fat(row.get('body_fat'))
    if bf_result:
        validated['body_fat_percentage'] = bf_result.value
    else:
        errors.append(bf_result.error)

    # Validate notes (optional)
    notes_result = validate_text(row.get('notes', ''), 'notes', allow_empty=True)
    if notes_result:
        validated['notes'] = sanitize_notes(notes_result.value)

    is_valid = len(errors) == 0
    return is_valid, validated, errors


def validate_workout_row(row: dict) -> Tuple[bool, dict, list]:
    """
    Validate a complete workout session row.

    Args:
        row: Dictionary with workout session data

    Returns:
        Tuple of (is_valid, validated_data, errors)
    """
    errors = []
    validated = {}

    # Validate date (required)
    date_result = validate_date(row.get('date', ''), 'session_date')
    if date_result:
        validated['session_date'] = date_result.value
    else:
        errors.append(date_result.error)
        return False, {}, errors

    # Validate exercise name (required)
    name_result = validate_text(row.get('exercise', ''), 'exercise_name', allow_empty=False, max_length=200)
    if name_result:
        validated['exercise_name'] = name_result.value
    else:
        errors.append(name_result.error)

    # Validate sets and reps
    sets_result = validate_sets_reps(row.get('sets'), 'sets')
    if sets_result:
        validated['sets'] = sets_result.value
    else:
        errors.append(sets_result.error)

    reps_result = validate_sets_reps(row.get('reps'), 'reps')
    if reps_result:
        validated['reps'] = reps_result.value
    else:
        errors.append(reps_result.error)

    # Validate notes
    notes_result = validate_text(row.get('notes', ''), 'notes', allow_empty=True)
    if notes_result:
        validated['notes'] = sanitize_notes(notes_result.value)

    is_valid = len(errors) == 0
    return is_valid, validated, errors


def validate_meal_row(row: dict) -> Tuple[bool, dict, list]:
    """
    Validate a complete meal log row.

    Args:
        row: Dictionary with meal log data

    Returns:
        Tuple of (is_valid, validated_data, errors)
    """
    errors = []
    validated = {}

    # Validate date (required)
    date_result = validate_date(row.get('date', ''), 'meal_date')
    if date_result:
        validated['meal_date'] = date_result.value
    else:
        errors.append(date_result.error)
        return False, {}, errors

    # Validate meal type (required)
    meal_type = row.get('meal_type', '').lower().strip()
    if not meal_type:
        errors.append("meal_type is required")
    else:
        validated['meal_type'] = meal_type

    # Validate calories
    cal_result = validate_calories(row.get('calories'))
    if cal_result:
        validated['calories'] = cal_result.value
    else:
        errors.append(cal_result.error)

    # Validate description
    desc_result = validate_text(row.get('description', ''), 'description', allow_empty=True)
    if desc_result:
        validated['description'] = sanitize_notes(desc_result.value)

    # Validate notes
    notes_result = validate_text(row.get('notes', ''), 'notes', allow_empty=True)
    if notes_result:
        validated['notes'] = sanitize_notes(notes_result.value)

    is_valid = len(errors) == 0
    return is_valid, validated, errors


if __name__ == '__main__':
    # Quick validation tests
    print("Running validation tests...")

    # Test date validation
    assert validate_date('2024-12-14', 'test_date').is_valid
    assert not validate_date('invalid', 'test_date').is_valid
    assert not validate_date('', 'test_date').is_valid

    # Test float validation
    assert validate_float('175.5', 'weight').value == 175.5
    assert validate_float('None', 'weight').value is None
    assert not validate_float('abc', 'weight').is_valid

    # Test weight validation
    assert validate_weight(175.5).is_valid
    assert validate_weight('None').is_valid
    assert not validate_weight(2000).is_valid  # Too high

    # Test body fat validation
    assert validate_body_fat(25.3).is_valid
    assert not validate_body_fat(150).is_valid  # Over 100%

    # Test sets/reps parsing
    sets, reps = parse_sets_reps_notation("3 sets of 10 reps")
    assert sets == 3 and reps == 10

    sets, reps = parse_sets_reps_notation("4x12")
    assert sets == 4 and reps == 12

    sets, reps = parse_sets_reps_notation("3 sets: 15, 12, 10 reps")
    assert sets == 3 and reps == 12  # Average

    print("All validation tests passed!")
