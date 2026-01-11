# Health and Fitness Goals

This directory contains all files and plans related to your health and fitness goals.

## User's Long-Term Goal
- **Starting Point:** 6'0", 300 lbs, 32.9% bodyfat.
- **Ultimate Goal:** Reduce weight to under 220 lbs and bodyfat to under 18%.

## Key Files

*   `docs/fitness-roadmap.md`: Your detailed, phased progression plan for achieving long-term fitness goals.
*   `docs/Full-Meal-Plan.md`: Your comprehensive meal plan.
*   `docs/Shopping-List-and-Estimate.md`: Your practical, standalone shopping list.
*   `data/check-in-log.md`: Your log of weigh-ins and body fat measurements.
*   `data/exercise-log.md`: Your log for tracking workout performance and progression.
*   `data/Coaching_sessions.md`: A log of coaching feedback and action plans.

## Reminders

*   **Weekly Weigh-In:** Every Monday morning.
*   **Monthly Body Fat Measurement:** On the first Monday of each month.
*   **Monthly Progress Photos:** On the first Monday of each month.

---
*   **Health and Fitness Curriculum Start Date:** 11/17/25
*   **Check-in Schedule:** Monday, Wednesday, Friday.

---

## Data Log Formatting Guide

This section provides instructions on how to format entries for the data log files located in the `data/` directory. All entries should be appended to the end of the respective file's table to maintain chronological order.

### `meal-log.md`

This file tracks daily food and drink intake. Each meal or snack is a new row in the table.

**Columns:**
*   `Date`: `YYYY-MM-DD`
*   `Meal`: `Breakfast`, `Lunch`, `Dinner`, `Snack`, etc.
*   `Food/Drink`: A description of the items consumed.
*   `Calories (est.)`: Estimated calories, prefixed with `~`.
*   `Notes`: Include Satiety scores (`Pre`, `Post`), Energy/Mood (`x/10`), and estimated protein (`Approx XXg protein`).

**Example Entry:**
```
| 2026-01-08 | Lunch | 8oz Costco Chipotle Grilled Chicken, half-portion rice & beans, on a bed of baby spinach. | ~620 | Satiety (Pre: 3, Post: 9), Energy/Mood: 8/10, Approx 73g protein |
```

**Daily Total:**
At the end of each day, add a summary row.
```
| **2026-01-08** | | **DAILY TOTAL** | **~2620** | **~233g protein** |
```

### `exercise-log.md`

This file tracks all workouts. Each exercise within a workout gets its own row.

**Columns:**
*   `Date`: `YYYY-MM-DD`
*   `Phase`: The current training phase (e.g., `Phase 1`).
*   `Workout`: The name of the workout (e.g., `Upper Body (Pull-up Focus)`).
*   `Exercise`: The specific exercise performed.
*   `Sets x Reps`: The sets and reps completed.
*   `Notes`: Any relevant notes on form, weight, difficulty, etc.

**Example Entry:**
```
| 2026-01-08 | Phase 1 | Upper Body (Pull-up Focus) | A: Pull-up Progression | 4 x 6 | 5 resistance bands |
| 2026-01-08 | Phase 1 | Daily Walk Progression | TrailViber Walking Pad | 2 hours | 2.5 mph, incline setting 2 |
```

### `check-in-log.md`

This file tracks weigh-ins and body measurements.

**Columns:**
*   `Date`: `YYYY-MM-DD`
*   `Weight (lbs)`: Weight in pounds.
*   `Body Fat %`: Body fat percentage.
*   `Waist (inches)`: Waist measurement at the navel.
*   `Chest (inches)`: Chest measurement.
*   `Notes`: Any relevant notes, e.g., "Initial Measurements".

**Example Entry:**
```
| 2026-01-05 | 304.5 | 34.4 | 51 | 52.5 | Initial Measurements |
```
