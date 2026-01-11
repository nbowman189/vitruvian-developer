#!/usr/bin/env python3
"""
Import the Nathan Recomposition Plan Phase 1 document into the database.
Run inside Docker container: docker exec -it primary-assistant-web python scripts/import_recomp_document.py
"""

import sys
import os

# Add the website directory to the path
sys.path.insert(0, '/app')

from website import create_app, db
from website.models import User, Document, DocumentType

# Document content
DOCUMENT_CONTENT = """# Nathan's 12-Week Recomposition Protocol: Phase 1

This is your comprehensive plan for the next 12 weeks. It is engineered based on your specific goals, schedule, and equipment. Your mission is to execute this plan with consistency. This document is your single source of truth.

## Primary 12-Week Objectives:
1.  **Performance Goal:** Achieve 1 unassisted, dead-hang pull-up.
2.  **Body Composition Goal:** Fit comfortably into your 2XL Joe A. Bank's sweater.
3.  **Weight Goal:** Reach a target weight of **285 lbs**.

---

## Part 1: The Nutrition Plan

This is the most critical area for your fat loss goal. Your previous intake of 3,000-3,400 calories is too high. We are establishing a new, disciplined baseline. Simplicity is key, so we'll use templates and your existing prep habits.

### Daily Targets:
*   **Calories:** **2,500 kcal**
*   **Protein:** **220g**

Don't worry as much about carbs and fats right now. **Your mission is to hit your calorie and protein targets every single day.**

### Sample Meal Structure:

**Breakfast: High-Protein Options (Prep-friendly)**
*   Your mission for breakfast is to hit a high protein number to fuel your morning and keep you full, without blowing the calorie budget. We're targeting **~600 calories** and **~60g of protein**. You have two primary options.

**Option 1: The "Greek Warrior" Protein Oats (Primary)**
*   This is fuel, designed to be made ahead of time so you can grab it and go. No cooking, no fuss.
*   **Batch Prep (4-5 servings):** In each container, combine 1/2 cup Rolled Oats, 1 scoop Protein Powder, 1 tbsp Chia Seeds, 1 cup Unsweetened Almond Milk, and 1 cup Plain Non-Fat Greek Yogurt.
*   **Execution:** Stir, seal, and refrigerate. Top with berries in the morning if desired.
*   *Estimated Macros: ~580 kcal, ~65g protein*

**Option 2: The "Engine Block" Casserole (Alternate)**
*   A hot, savory meal that leverages existing prep. Cook once, eat all week.
*   **Batch Prep (4 servings):** Whisk 12 whole eggs, 2 cups liquid egg whites, and 1 cup blended low-fat cottage cheese. Pour over a 9x13 dish containing 2 lbs of diced, pre-cooked protein (e.g., chipotle chicken, lean steak) and chopped veggies. Bake at 375°F (190°C) for 30-40 mins.
*   **Execution:** Cut into 4 servings. Microwave one for 90 seconds.
*   *Estimated Macros (with 2lbs chipotle chicken): ~587 kcal, ~77g protein*

**Option 3: "Power Builder Breakfast"**
*   **Components:** 2 whole eggs, 3/4 cup liquid egg whites, 4oz Chipotle Chicken, 1 Chobani vanilla Greek yogurt cup, 2 tbsp Quaker granola.
*   *Estimated Macros: ~618 kcal, ~61g protein*

**Lunch: Protein & Greens Template (Simple & Fast)**
*   **Formula:** 1-2 portions of lean protein + 1-2 cups of green vegetables.
*   **Example 1 (Standard):** 8 oz grilled chicken breast strips (buy pre-cooked) + a bag of microwavable steamed broccoli.
*   **Example 2 (Optimal Prep-Friendly):** Combine a half-portion of your pre-cooked rice & beans with 6 oz of grilled chicken breast strips. This can be served over a bed of baby spinach.
*   *Estimated Macros for Example 2: ~563 kcal, ~58g protein*

**Dinner: The Recomp Salad**
*   **Modification:** Keep your big salad, but swap the 8oz breaded chicken for 8oz of grilled chicken. For dressing, switch to a Greek yogurt-based ranch or a light vinaigrette.
*   *Estimated Macros: ~650 kcal, ~60g protein*

**Snacks / Protein Shake:**
*   **Hard-Boiled Eggs:** Prep these. Two eggs are ~150 kcal and 12g protein.
*   **Hard-Boiled Eggs + Fruit + Nuts:** Two hard-boiled eggs, one large apple, and a handful of almonds (~405 kcal, ~18g protein).
*   **The Sustainable Protein Shake:** You need a go-to recipe. This is non-negotiable for hitting 220g of protein.
    *   2 scoops Orgain Plant-Based Protein Powder (or similar)
    *   12 oz Unsweetened Almond Milk
    *   1 large handful of spinach (you will not taste it)
    *   1/2 banana or 1 cup of berries
    *   1/2 cup rolled oats
    *   2 tbsp peanut butter
    *   *Estimated Macros (Super-Shake): ~790 kcal, ~57g protein (with oats & peanut butter)*

---

## Part 2: The Workout Plan (4-Day Upper/Lower Split)

*   **Schedule:** 4 days/week for 60 minutes. Example: Mon(Upper), Tue(Lower), Thu(Upper), Fri(Lower).
*   **Core Principle:** Progressive Overload. Your job is to get stronger. Log every workout. Once you can hit the top of the rep range for all sets, increase the weight or use a more difficult progression/band.

### Day 1 & 3: Upper Body (Pull-up Focus)

| Exercise | Sets x Reps | Notes |
| :--- | :--- | :--- |
| **A: Pull-up Progression** | 4 x 6-8 | **This is the priority.** Start with **Band-Assisted Pull-ups**. Choose a band that makes 6 reps challenging. Your goal is to use thinner bands over time. |
| **B: Ring Push-ups** | 4 x 8-12 | Focus on deep reps. Elevate your feet to make it harder as you get stronger. |
| **C1: Dumbbell Rows** | 3 x 10-15 | Use your 20lb dumbbells. Focus on squeezing your shoulder blades. |
| **C2: Dumbbell Overhead Press** | 3 x 10-15 | Seated or standing. Controlled movements. |
| **D: Active/Passive Hang** | 3 x 30-45 sec | After your last set, just hang from the bar for as long as possible to build grip strength. |

*(Note on C1/C2: These are a "superset." Do a set of C1, rest 60s, do a set of C2, rest 60s, repeat.)*

### Day 2 & 4: Lower Body & Core

| Exercise | Sets x Reps | Notes |
| :--- | :--- | :--- |
| **A: Goblet Squats** | 4 x 10-15 | Use your heaviest dumbbell. Focus on going deep while keeping your chest up. |
| **B: Dumbbell Romanian Deadlifts**| 4 x 12-15 | Use your 20lb dumbbells. Hinge at the hips, feel the stretch in your hamstrings. |
| **C: Walking Lunges** | 3 x 20 (total) | Can be done with or without dumbbells. |
| **D1: Ab Wheel Rollouts** | 3 x 8-15 | Go as far as you can with good form. If you don't have a wheel, do Planks for 60s. |
| **D2: Kettlebell Swings** | 3 x 15-20 | Start with the 20 or 25lb KB. This is a conditioning finisher. Focus on explosive hip hinge form. |

---

## Part 3: Goals & Tracking Protocol

This is how we measure success and stay on track.

### The Pull-up Ladder:
Your path to one pull-up is a step-by-step process.
*   **Level 1 (Current):** Band-Assisted Pull-ups (4x6-8 reps). Master this.
*   **Level 2:** Negative Pull-ups. Jump to the top of the bar and lower yourself down as slowly as possible (aim for 5-10 seconds). Do 4 sets of 3-5 reps.
*   **Level 3:** First Unassisted Rep.

### Tracking:
*   **Weight:** Weigh yourself 3-4 times per week (e.g., Mon, Wed, Fri morning) and take the weekly average. Don't obsess over daily changes.
*   **Measurements:** Every 2 weeks, on a Sunday morning, take a photo from the front, side, and back. Measure your waist at the navel.
*   **The Sweater Test:** Try on the 2XL sweater every 4 weeks. Note the change in fit.
*   **Logs:** Log every workout and every meal. This data is how we make adjustments. If you stall for 2 weeks, we will use the logs to identify the problem and fix it.

This is your plan. It is a direct reflection of your goals and the principles of effective recomposition. The plan is engineered for success. Now, you just have to execute.
"""

def import_document():
    """Import the recomposition plan document."""
    app = create_app()

    with app.app_context():
        # Find the admin user (user_id=1)
        user = User.query.filter_by(id=1).first()
        if not user:
            print("Error: No user with id=1 found. Please create an admin user first.")
            return False

        # Check if document already exists
        existing = Document.query.filter_by(
            user_id=user.id,
            slug='nathans-12-week-recomposition-protocol-phase-1'
        ).first()

        if existing:
            print(f"Document already exists with id={existing.id}. Updating content...")
            existing.content = DOCUMENT_CONTENT
            existing.title = "Nathan's 12-Week Recomposition Protocol: Phase 1"
            existing.summary = "Comprehensive 12-week body recomposition plan with nutrition targets (2500 kcal, 220g protein), 4-day upper/lower workout split focused on pull-up progression, and tracking protocols."
            existing.document_type = DocumentType.FITNESS_ROADMAP
            existing.tags = ['recomposition', 'nutrition', 'workout-plan', 'pull-ups', 'phase-1', '12-week']
            existing.source = 'import'
            existing.metadata_json = {
                'duration_weeks': 12,
                'phase': 1,
                'calorie_target': 2500,
                'protein_target': 220,
                'workout_days': 4,
                'primary_goal': 'recomposition',
                'performance_goal': '1 unassisted pull-up',
                'weight_goal': 285
            }
            db.session.commit()
            print(f"Updated document id={existing.id}")
            return True

        # Create new document
        doc = Document(
            user_id=user.id,
            title="Nathan's 12-Week Recomposition Protocol: Phase 1",
            slug='nathans-12-week-recomposition-protocol-phase-1',
            document_type=DocumentType.FITNESS_ROADMAP,
            content=DOCUMENT_CONTENT,
            summary="Comprehensive 12-week body recomposition plan with nutrition targets (2500 kcal, 220g protein), 4-day upper/lower workout split focused on pull-up progression, and tracking protocols.",
            tags=['recomposition', 'nutrition', 'workout-plan', 'pull-ups', 'phase-1', '12-week'],
            source='import',
            is_public=False,
            is_archived=False,
            metadata_json={
                'duration_weeks': 12,
                'phase': 1,
                'calorie_target': 2500,
                'protein_target': 220,
                'workout_days': 4,
                'primary_goal': 'recomposition',
                'performance_goal': '1 unassisted pull-up',
                'weight_goal': 285
            }
        )

        db.session.add(doc)
        db.session.commit()

        print(f"Successfully created document:")
        print(f"  ID: {doc.id}")
        print(f"  Title: {doc.title}")
        print(f"  Slug: {doc.slug}")
        print(f"  Type: {doc.document_type.value}")
        print(f"  Tags: {doc.tags}")

        return True

if __name__ == '__main__':
    success = import_document()
    sys.exit(0 if success else 1)
