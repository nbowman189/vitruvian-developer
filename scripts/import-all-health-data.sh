#!/bin/bash
# Master script to import all health data from markdown files to database
# Run this script to import health metrics, meal logs, exercise logs, and coaching sessions

set -e  # Exit on error

echo "======================================"
echo "Health Data Import - All Files"
echo "======================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/Health_and_Fitness/data"

echo "📂 Project root: $PROJECT_ROOT"
echo "📂 Data directory: $DATA_DIR"
echo ""

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo "❌ Data directory not found: $DATA_DIR"
    exit 1
fi

# Function to run import script
run_import() {
    local script_name=$1
    local data_file=$2
    local description=$3

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📥 Importing: $description"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    if [ -f "$DATA_DIR/$data_file" ]; then
        python3 "$SCRIPT_DIR/$script_name" "$DATA_DIR/$data_file"
        echo ""
    else
        echo "⚠️  File not found: $data_file (skipping)"
        echo ""
    fi
}

# Import in order
run_import "import-health-data.py" "check-in-log.md" "Health Metrics (Weight, Body Fat, BMI)"
run_import "import-meal-log.py" "meal-log.md" "Meal Logs (Daily Nutrition)"
run_import "import-exercise-log.py" "exercise-log.md" "Exercise Logs (Workout Sessions)"
run_import "import-coaching-sessions.py" "Coaching_sessions.md" "Coaching Sessions"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All imports complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 To verify imported data, run:"
echo ""
echo "   # Check health metrics"
echo "   docker-compose exec web python -c \"from website import create_app, db; from website.models.health import HealthMetric; app = create_app(); app.app_context().push(); print(f'Health metrics: {HealthMetric.query.count()}')\""
echo ""
echo "   # Check meal logs"
echo "   docker-compose exec web python -c \"from website import create_app, db; from website.models.nutrition import MealLog; app = create_app(); app.app_context().push(); print(f'Meal logs: {MealLog.query.count()}')\""
echo ""
echo "   # Check workout sessions"
echo "   docker-compose exec web python -c \"from website import create_app, db; from website.models.workout import WorkoutSession; app = create_app(); app.app_context().push(); print(f'Workout sessions: {WorkoutSession.query.count()}')\""
echo ""
echo "   # Check coaching sessions"
echo "   docker-compose exec web python -c \"from website import create_app, db; from website.models.coaching import CoachingSession; app = create_app(); app.app_context().push(); print(f'Coaching sessions: {CoachingSession.query.count()}')\""
echo ""
