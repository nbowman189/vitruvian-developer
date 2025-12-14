"""
Nutrition API
=============

RESTful API endpoints for meal and nutrition tracking.

Endpoints:
- GET    /api/nutrition/meals              - List meal logs
- POST   /api/nutrition/meals              - Create meal log
- GET    /api/nutrition/meals/<id>         - Get specific meal
- PUT    /api/nutrition/meals/<id>         - Update meal
- DELETE /api/nutrition/meals/<id>         - Delete meal
- GET    /api/nutrition/daily-summary      - Get daily nutrition summary
- GET    /api/nutrition/weekly-summary     - Get weekly nutrition summary
"""

from flask import Blueprint, request
from flask_login import current_user
from sqlalchemy import func, and_
from datetime import datetime, timedelta

from ..models import db
from ..models.nutrition import MealLog, MealType, AdherenceLevel
from . import (
    success_response,
    error_response,
    paginated_response,
    require_active_user,
    validate_request_data,
    validate_pagination_params,
    validate_date_range_params,
    validate_date_format,
    logger
)

# Create nutrition API sub-blueprint
nutrition_api_bp = Blueprint('nutrition_api', __name__, url_prefix='/nutrition')


@nutrition_api_bp.route('/meals', methods=['GET'])
@require_active_user
def get_meals():
    """
    Get meal logs for authenticated user.

    Query Parameters:
        - page, per_page, start_date, end_date, meal_type, sort

    Returns:
        200: Paginated list of meal logs
    """
    page, per_page = validate_pagination_params()

    is_valid, start_date, end_date, error_msg = validate_date_range_params()
    if not is_valid:
        return error_response(error_msg, status_code=400)

    sort_order = request.args.get('sort', 'desc').lower()

    # Build query
    query = MealLog.query.filter_by(user_id=current_user.id)

    if start_date:
        query = query.filter(MealLog.meal_date >= start_date)
    if end_date:
        query = query.filter(MealLog.meal_date <= end_date)

    # Filter by meal type
    meal_type = request.args.get('meal_type')
    if meal_type:
        try:
            type_enum = MealType(meal_type)
            query = query.filter(MealLog.meal_type == type_enum)
        except ValueError:
            return error_response(f"Invalid meal_type: {meal_type}", status_code=400)

    # Apply sorting
    if sort_order == 'asc':
        query = query.order_by(MealLog.meal_date.asc(), MealLog.meal_time.asc())
    else:
        query = query.order_by(MealLog.meal_date.desc(), MealLog.meal_time.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    meals = [meal.to_dict() for meal in pagination.items]

    return paginated_response(
        items=meals,
        page=page,
        per_page=per_page,
        total=pagination.total
    )


@nutrition_api_bp.route('/meals', methods=['POST'])
@require_active_user
def create_meal():
    """
    Create a new meal log.

    Request Body:
        - meal_date (str, required): Meal date (YYYY-MM-DD)
        - meal_type (str, required): Meal type
        - meal_time (str, optional): Meal time (HH:MM:SS)
        - calories (int, optional): Total calories
        - protein_g (float, optional): Protein in grams
        - carbs_g (float, optional): Carbs in grams
        - fat_g (float, optional): Fat in grams
        - fiber_g (float, optional): Fiber in grams
        - sugar_g (float, optional): Sugar in grams
        - sodium_mg (int, optional): Sodium in mg
        - water_oz (float, optional): Water in oz
        - description (str, optional): Meal description
        - foods (str, optional): Foods consumed
        - recipe_name (str, optional): Recipe name
        - adherence_to_plan (str, optional): Adherence level
        - planned_meal (bool, optional): Was this planned?
        - satisfaction (int, optional): Satisfaction (1-10)
        - hunger_before (int, optional): Hunger before (1-10)
        - hunger_after (int, optional): Hunger after (1-10)
        - notes (str, optional): Notes

    Returns:
        201: Created meal log
    """
    required_fields = ['meal_date', 'meal_type']
    optional_fields = [
        'meal_time', 'calories', 'protein_g', 'carbs_g', 'fat_g', 'fiber_g',
        'sugar_g', 'sodium_mg', 'water_oz', 'description', 'foods', 'recipe_name',
        'adherence_to_plan', 'planned_meal', 'satisfaction', 'hunger_before',
        'hunger_after', 'notes'
    ]

    is_valid, result = validate_request_data(required_fields, optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    # Validate date
    is_valid, date_obj = validate_date_format(data['meal_date'])
    if not is_valid:
        return error_response(date_obj, status_code=400)
    data['meal_date'] = date_obj

    # Validate meal time if provided
    if 'meal_time' in data and data['meal_time']:
        try:
            from datetime import time as time_class
            time_parts = data['meal_time'].split(':')
            time_obj = time_class(int(time_parts[0]), int(time_parts[1]))
            data['meal_time'] = time_obj
        except (ValueError, IndexError):
            return error_response("Invalid meal_time format. Expected HH:MM", status_code=400)

    # Validate meal type
    try:
        type_enum = MealType(data['meal_type'])
    except ValueError:
        valid_types = [t.value for t in MealType]
        return error_response(
            f"Invalid meal_type. Must be one of: {', '.join(valid_types)}",
            status_code=400
        )

    # Validate adherence level if provided
    if 'adherence_to_plan' in data and data['adherence_to_plan']:
        try:
            data['adherence_to_plan'] = AdherenceLevel(data['adherence_to_plan'])
        except ValueError:
            valid_levels = [a.value for a in AdherenceLevel]
            return error_response(
                f"Invalid adherence_to_plan. Must be one of: {', '.join(valid_levels)}",
                status_code=400
            )

    try:
        meal = MealLog(
            user_id=current_user.id,
            meal_type=type_enum,
            **{k: v for k, v in data.items() if k != 'meal_type'}
        )

        db.session.add(meal)
        db.session.commit()

        logger.info(f'User {current_user.id} created meal log {meal.id}')

        return success_response(
            data=meal.to_dict(),
            message='Meal log created successfully',
            status_code=201
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating meal log: {e}', exc_info=True)
        return error_response('Failed to create meal log', errors=[str(e)], status_code=500)


@nutrition_api_bp.route('/meals/<int:meal_id>', methods=['GET'])
@require_active_user
def get_meal(meal_id):
    """Get a specific meal log."""
    meal = MealLog.query.filter_by(
        id=meal_id,
        user_id=current_user.id
    ).first()

    if not meal:
        return error_response('Meal log not found', status_code=404)

    return success_response(
        data=meal.to_dict(),
        message='Meal log retrieved successfully'
    )


@nutrition_api_bp.route('/meals/<int:meal_id>', methods=['PUT'])
@require_active_user
def update_meal(meal_id):
    """Update a meal log."""
    meal = MealLog.query.filter_by(
        id=meal_id,
        user_id=current_user.id
    ).first()

    if not meal:
        return error_response('Meal log not found', status_code=404)

    optional_fields = [
        'meal_date', 'meal_type', 'meal_time', 'calories', 'protein_g', 'carbs_g',
        'fat_g', 'fiber_g', 'sugar_g', 'sodium_mg', 'water_oz', 'description',
        'foods', 'recipe_name', 'adherence_to_plan', 'planned_meal', 'satisfaction',
        'hunger_before', 'hunger_after', 'notes'
    ]

    is_valid, result = validate_request_data(required_fields=None, optional_fields=optional_fields)
    if not is_valid:
        return error_response(**result, status_code=400)

    data = result

    # Validate date if provided
    if 'meal_date' in data:
        is_valid, date_obj = validate_date_format(data['meal_date'])
        if not is_valid:
            return error_response(date_obj, status_code=400)
        data['meal_date'] = date_obj

    # Validate meal time if provided
    if 'meal_time' in data and data['meal_time']:
        try:
            from datetime import time as time_class
            time_parts = data['meal_time'].split(':')
            time_obj = time_class(int(time_parts[0]), int(time_parts[1]))
            data['meal_time'] = time_obj
        except (ValueError, IndexError):
            return error_response("Invalid meal_time format. Expected HH:MM", status_code=400)

    # Validate enums if provided
    if 'meal_type' in data:
        try:
            data['meal_type'] = MealType(data['meal_type'])
        except ValueError:
            return error_response("Invalid meal_type", status_code=400)

    if 'adherence_to_plan' in data and data['adherence_to_plan']:
        try:
            data['adherence_to_plan'] = AdherenceLevel(data['adherence_to_plan'])
        except ValueError:
            return error_response("Invalid adherence_to_plan", status_code=400)

    try:
        for key, value in data.items():
            setattr(meal, key, value)

        db.session.commit()

        logger.info(f'User {current_user.id} updated meal log {meal_id}')

        return success_response(
            data=meal.to_dict(),
            message='Meal log updated successfully'
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating meal log: {e}', exc_info=True)
        return error_response('Failed to update meal log', errors=[str(e)], status_code=500)


@nutrition_api_bp.route('/meals/<int:meal_id>', methods=['DELETE'])
@require_active_user
def delete_meal(meal_id):
    """Delete a meal log."""
    meal = MealLog.query.filter_by(
        id=meal_id,
        user_id=current_user.id
    ).first()

    if not meal:
        return error_response('Meal log not found', status_code=404)

    try:
        db.session.delete(meal)
        db.session.commit()

        logger.info(f'User {current_user.id} deleted meal log {meal_id}')

        return success_response(message='Meal log deleted successfully')

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting meal log: {e}', exc_info=True)
        return error_response('Failed to delete meal log', errors=[str(e)], status_code=500)


@nutrition_api_bp.route('/daily-summary', methods=['GET'])
@require_active_user
def get_daily_summary():
    """
    Get nutrition summary for a specific day.

    Query Parameters:
        - date (str): Date to summarize (YYYY-MM-DD, default: today)

    Returns:
        200: Daily nutrition summary
    """
    # Get date parameter or use today
    date_str = request.args.get('date')
    if date_str:
        is_valid, date_obj = validate_date_format(date_str)
        if not is_valid:
            return error_response(date_obj, status_code=400)
    else:
        date_obj = datetime.now().date()

    # Get all meals for this date
    meals = MealLog.query.filter_by(
        user_id=current_user.id,
        meal_date=date_obj
    ).order_by(MealLog.meal_time.asc()).all()

    if not meals:
        return success_response(data={
            'date': date_obj.isoformat(),
            'total_meals': 0,
            'message': 'No meals logged for this date'
        })

    # Calculate totals
    total_calories = sum(m.calories for m in meals if m.calories) or 0
    total_protein = sum(m.protein_g for m in meals if m.protein_g) or 0
    total_carbs = sum(m.carbs_g for m in meals if m.carbs_g) or 0
    total_fat = sum(m.fat_g for m in meals if m.fat_g) or 0
    total_fiber = sum(m.fiber_g for m in meals if m.fiber_g) or 0
    total_water = sum(m.water_oz for m in meals if m.water_oz) or 0

    # Calculate macro percentages
    protein_cal = total_protein * 4
    carbs_cal = total_carbs * 4
    fat_cal = total_fat * 9
    total_macro_cal = protein_cal + carbs_cal + fat_cal

    if total_macro_cal > 0:
        protein_pct = (protein_cal / total_macro_cal) * 100
        carbs_pct = (carbs_cal / total_macro_cal) * 100
        fat_pct = (fat_cal / total_macro_cal) * 100
        macro_ratio = f"{protein_pct:.0f}/{carbs_pct:.0f}/{fat_pct:.0f}"
    else:
        protein_pct = carbs_pct = fat_pct = None
        macro_ratio = None

    # Count planned vs unplanned meals
    planned_count = sum(1 for m in meals if m.planned_meal)
    unplanned_count = len(meals) - planned_count

    summary = {
        'date': date_obj.isoformat(),
        'total_meals': len(meals),
        'nutrition_totals': {
            'calories': total_calories,
            'protein_g': round(total_protein, 1),
            'carbs_g': round(total_carbs, 1),
            'fat_g': round(total_fat, 1),
            'fiber_g': round(total_fiber, 1),
            'water_oz': round(total_water, 1),
        },
        'macronutrient_breakdown': {
            'protein_percentage': round(protein_pct, 1) if protein_pct else None,
            'carbs_percentage': round(carbs_pct, 1) if carbs_pct else None,
            'fat_percentage': round(fat_pct, 1) if fat_pct else None,
            'ratio': macro_ratio,
        },
        'meal_planning': {
            'planned_meals': planned_count,
            'unplanned_meals': unplanned_count,
            'adherence_rate': round((planned_count / len(meals)) * 100, 1) if meals else 0,
        },
        'meals': [meal.to_dict() for meal in meals]
    }

    return success_response(data=summary, message=f'Daily summary for {date_obj}')


@nutrition_api_bp.route('/weekly-summary', methods=['GET'])
@require_active_user
def get_weekly_summary():
    """
    Get nutrition summary for a week.

    Query Parameters:
        - start_date (str): Week start date (YYYY-MM-DD, default: 7 days ago)

    Returns:
        200: Weekly nutrition summary
    """
    # Get start date or default to 7 days ago
    start_date_str = request.args.get('start_date')
    if start_date_str:
        is_valid, start_date = validate_date_format(start_date_str)
        if not is_valid:
            return error_response(start_date, status_code=400)
    else:
        start_date = datetime.now().date() - timedelta(days=7)

    end_date = start_date + timedelta(days=6)

    # Get all meals in date range
    meals = MealLog.query.filter(
        and_(
            MealLog.user_id == current_user.id,
            MealLog.meal_date >= start_date,
            MealLog.meal_date <= end_date
        )
    ).all()

    if not meals:
        return success_response(data={
            'period': {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat()},
            'total_meals': 0,
            'message': 'No meals logged for this week'
        })

    # Calculate totals
    total_calories = sum(m.calories for m in meals if m.calories) or 0
    total_protein = sum(m.protein_g for m in meals if m.protein_g) or 0
    total_carbs = sum(m.carbs_g for m in meals if m.carbs_g) or 0
    total_fat = sum(m.fat_g for m in meals if m.fat_g) or 0

    # Calculate daily averages
    days = 7
    avg_calories = total_calories / days
    avg_protein = total_protein / days
    avg_carbs = total_carbs / days
    avg_fat = total_fat / days

    # Count planned meals
    planned_count = sum(1 for m in meals if m.planned_meal)
    adherence_rate = (planned_count / len(meals)) * 100 if meals else 0

    # Group by day
    daily_breakdown = {}
    for meal in meals:
        date_str = meal.meal_date.isoformat()
        if date_str not in daily_breakdown:
            daily_breakdown[date_str] = {
                'date': date_str,
                'meals': [],
                'total_calories': 0,
                'total_protein': 0,
                'total_carbs': 0,
                'total_fat': 0,
            }

        daily_breakdown[date_str]['meals'].append(meal.to_dict(include_calculated=False))
        daily_breakdown[date_str]['total_calories'] += meal.calories or 0
        daily_breakdown[date_str]['total_protein'] += meal.protein_g or 0
        daily_breakdown[date_str]['total_carbs'] += meal.carbs_g or 0
        daily_breakdown[date_str]['total_fat'] += meal.fat_g or 0

    summary = {
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': days
        },
        'total_meals': len(meals),
        'weekly_totals': {
            'calories': total_calories,
            'protein_g': round(total_protein, 1),
            'carbs_g': round(total_carbs, 1),
            'fat_g': round(total_fat, 1),
        },
        'daily_averages': {
            'calories': round(avg_calories, 1),
            'protein_g': round(avg_protein, 1),
            'carbs_g': round(avg_carbs, 1),
            'fat_g': round(avg_fat, 1),
        },
        'adherence': {
            'planned_meals': planned_count,
            'total_meals': len(meals),
            'adherence_rate': round(adherence_rate, 1),
        },
        'daily_breakdown': list(daily_breakdown.values())
    }

    return success_response(data=summary, message=f'Weekly summary from {start_date} to {end_date}')
