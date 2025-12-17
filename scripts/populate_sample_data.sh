#!/bin/bash
# Populate sample data via API calls

BASE_URL="http://localhost:8001"
COOKIE_FILE="/tmp/primary_assistant_cookies.txt"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Logging in...${NC}"

# Login to get session cookie
LOGIN_RESPONSE=$(curl -s -c "$COOKIE_FILE" -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username_or_email=admin" \
  -d "password=admin123" \
  -d "remember_me=false" \
  -w "\n%{http_code}")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -1)

if [ "$HTTP_CODE" != "302" ] && [ "$HTTP_CODE" != "200" ]; then
    echo -e "${RED}❌ Login failed (HTTP $HTTP_CODE)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Logged in successfully${NC}\n"

# Function to make authenticated POST request
api_post() {
    local endpoint=$1
    local data=$2

    response=$(curl -s -b "$COOKIE_FILE" -X POST "$BASE_URL$endpoint" \
      -H "Content-Type: application/json" \
      -d "$data" \
      -w "\n%{http_code}")

    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" =~ ^2 ]]; then
        echo -e "${GREEN}  ✓ Success${NC}"
        return 0
    else
        echo -e "${RED}  ✗ Failed (HTTP $http_code)${NC}"
        echo "    Response: $body"
        return 1
    fi
}

# Add health metrics for the past 7 days
echo -e "${BLUE}📊 Adding health metrics...${NC}"
for i in {0..6}; do
    date=$(date -v-${i}d +%Y-%m-%d 2>/dev/null || date -d "$i days ago" +%Y-%m-%d 2>/dev/null)
    weight=$(echo "180 - $i * 0.5" | bc)
    bodyfat=$(echo "20 - $i * 0.2" | bc)

    echo "  Day $((i+1)): $date"
    api_post "/api/health/metrics" "{
        \"recorded_date\": \"$date\",
        \"weight_lbs\": $weight,
        \"body_fat_percentage\": $bodyfat,
        \"energy_level\": 8,
        \"mood\": 8,
        \"sleep_quality\": 7
    }"
done

# Add workout sessions
echo -e "\n${BLUE}💪 Adding workout sessions...${NC}"
for i in 0 2 4 6; do
    date=$(date -v-${i}d +%Y-%m-%d 2>/dev/null || date -d "$i days ago" +%Y-%m-%d 2>/dev/null)

    if [ $((i % 4)) -eq 0 ]; then
        session_type="strength"
        name="Upper Body Strength"
        duration=60
    else
        session_type="cardio"
        name="Cardio Session"
        duration=30
    fi

    echo "  $name on $date"
    api_post "/api/workouts" "{
        \"session_date\": \"$date\",
        \"session_type\": \"$session_type\",
        \"name\": \"$name\",
        \"duration_minutes\": $duration,
        \"intensity\": 8
    }"
done

# Add nutrition logs (3 meals per day for 7 days)
echo -e "\n${BLUE}🍽️  Adding nutrition logs...${NC}"
for i in {0..6}; do
    date=$(date -v-${i}d +%Y-%m-%d 2>/dev/null || date -d "$i days ago" +%Y-%m-%d 2>/dev/null)
    echo "  Meals for $date"

    # Breakfast
    api_post "/api/nutrition/meals" "{
        \"meal_date\": \"$date\",
        \"meal_type\": \"breakfast\",
        \"meal_name\": \"Breakfast\",
        \"calories\": 500,
        \"protein_g\": 30,
        \"carbs_g\": 50,
        \"fat_g\": 15,
        \"planned_meal\": true
    }"

    # Lunch
    api_post "/api/nutrition/meals" "{
        \"meal_date\": \"$date\",
        \"meal_type\": \"lunch\",
        \"meal_name\": \"Lunch\",
        \"calories\": 600,
        \"protein_g\": 40,
        \"carbs_g\": 60,
        \"fat_g\": 20,
        \"planned_meal\": true
    }"

    # Dinner
    api_post "/api/nutrition/meals" "{
        \"meal_date\": \"$date\",
        \"meal_type\": \"dinner\",
        \"meal_name\": \"Dinner\",
        \"calories\": 700,
        \"protein_g\": 50,
        \"carbs_g\": 70,
        \"fat_g\": 25,
        \"planned_meal\": true
    }"
done

# Add coaching sessions
echo -e "\n${BLUE}🎯 Adding coaching sessions...${NC}"

# Past session
past_date=$(date -v-5d +%Y-%m-%d 2>/dev/null || date -d "5 days ago" +%Y-%m-%d 2>/dev/null)
echo "  Past session: $past_date"
api_post "/api/coaching/sessions" "{
    \"session_date\": \"$past_date\",
    \"coach_name\": \"Coach Alex\",
    \"focus_areas\": \"Progressive overload and nutrition consistency\",
    \"notes\": \"Great progress this week! Keep pushing.\",
    \"action_items\": \"Continue current program, add 5lbs to major lifts\"
}"

# Future session
future_date=$(date -v+3d +%Y-%m-%d 2>/dev/null || date -d "3 days" +%Y-%m-%d 2>/dev/null)
echo "  Future session: $future_date"
api_post "/api/coaching/sessions" "{
    \"session_date\": \"$future_date\",
    \"coach_name\": \"Coach Alex\",
    \"focus_areas\": \"Check-in and program adjustment\"
}"

# Add goals
echo -e "\n${BLUE}🎯 Adding goals...${NC}"

target_date=$(date -v+30d +%Y-%m-%d 2>/dev/null || date -d "30 days" +%Y-%m-%d 2>/dev/null)

echo "  Goal 1: Weight loss"
api_post "/api/coaching/goals" "{
    \"title\": \"Reach 175 lbs\",
    \"description\": \"Weight loss goal\",
    \"target_date\": \"$target_date\",
    \"status\": \"active\",
    \"progress_percentage\": 25
}"

echo "  Goal 2: Strength"
api_post "/api/coaching/goals" "{
    \"title\": \"Bench Press 225 lbs\",
    \"description\": \"Strength goal\",
    \"target_date\": \"$target_date\",
    \"status\": \"active\",
    \"progress_percentage\": 40
}"

echo "  Goal 3: Cardio"
api_post "/api/coaching/goals" "{
    \"title\": \"Run 5K under 25 minutes\",
    \"description\": \"Cardio goal\",
    \"target_date\": \"$target_date\",
    \"status\": \"active\",
    \"progress_percentage\": 30
}"

echo -e "\n${GREEN}✅ Sample data created successfully!${NC}"
echo -e "\n📊 Summary:"
echo "  - Health metrics: 7 days"
echo "  - Workouts: 4 sessions"
echo "  - Nutrition: 21 meals (3/day × 7 days)"
echo "  - Coaching: 2 sessions (1 past, 1 future)"
echo "  - Goals: 3 active goals"
echo -e "\n🌐 Dashboard: http://localhost:8001/dashboard"

# Cleanup
rm -f "$COOKIE_FILE"
