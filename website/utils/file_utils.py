"""
File utilities for handling markdown files and project data
"""

import os
import re
import markdown
from datetime import datetime


class BlogPostParser:
    """Parses blog post markdown files with YAML front matter"""

    @staticmethod
    def parse(filepath):
        """
        Parse a blog post markdown file with YAML front matter.

        Returns:
            dict: Parsed post data with metadata and HTML content
        """
        with open(filepath, 'r') as f:
            content = f.read()

        # Extract YAML front matter
        match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
        if not match:
            return None

        metadata_str, body = match.groups()
        metadata = BlogPostParser._parse_metadata(metadata_str)

        return {
            'metadata': metadata,
            'content': body.strip(),
            'html': markdown.markdown(body.strip(), extensions=['tables', 'codehilite'])
        }

    @staticmethod
    def _parse_metadata(metadata_str):
        """Parse YAML-like metadata string"""
        metadata = {}

        for line in metadata_str.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Parse lists
                if value.startswith('[') and value.endswith(']'):
                    value = [item.strip().strip("'\"") for item in value[1:-1].split(',')]
                # Parse booleans and numbers
                elif value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)

                metadata[key] = value

        return metadata


class ProjectFileManager:
    """Manages project files and directories"""

    # Virtual database-driven pages for Health_and_Fitness project
    VIRTUAL_PAGES = {
        'Health_and_Fitness': [
            'data/health-metrics-log.md',
            'data/workout-log.md',
            'data/meal-log.md',
            'data/progress-photos.md',
            'data/coaching-sessions.md'
        ]
    }

    def __init__(self, project_root, project_dirs, allow_data_access=False):
        self.project_root = project_root
        self.project_dirs = project_dirs
        self.allow_data_access = allow_data_access

    def get_project_files(self, project_name, file_order=None):
        """
        Get all markdown files for a project, including virtual database-driven pages.

        Args:
            project_name: Name of the project
            file_order: List specifying desired file ordering

        Returns:
            list: Sorted list of markdown file paths
        """
        if project_name not in self.project_dirs:
            raise ValueError(f"Project '{project_name}' not found")

        project_path = os.path.join(self.project_root, project_name)
        markdown_files = []

        for root, _, files in os.walk(project_path):
            for file in files:
                if file.endswith('.md'):
                    relative_path = os.path.relpath(os.path.join(root, file), project_path)
                    markdown_files.append(relative_path)

        # Add virtual database-driven pages if data access is allowed
        if self.allow_data_access and project_name in self.VIRTUAL_PAGES:
            markdown_files.extend(self.VIRTUAL_PAGES[project_name])

        # Apply custom ordering if provided
        if file_order:
            markdown_files.sort(key=lambda f: (
                file_order.index(f) if f in file_order else len(file_order)
            ))

        return markdown_files

    def get_file_content(self, project_name, file_path):
        """
        Get content of a specific file or generate virtual database-driven page.

        Args:
            project_name: Name of the project
            file_path: Path to the file within the docs/ subdirectory (or data/ if allow_data_access=True)

        Returns:
            str: File content or generated content for virtual pages
        """
        if project_name not in self.project_dirs:
            raise ValueError(f"Project '{project_name}' not found")

        # Check if this is a virtual database-driven page
        if (self.allow_data_access and
            project_name in self.VIRTUAL_PAGES and
            file_path in self.VIRTUAL_PAGES[project_name]):
            return self._generate_virtual_page_content(project_name, file_path)

        project_path = os.path.realpath(os.path.join(self.project_root, project_name))

        # Build search paths based on allow_data_access flag
        search_paths = [os.path.join(project_path, 'docs')]

        if self.allow_data_access:
            search_paths.append(os.path.join(project_path, 'data'))

        search_paths.append(project_path)  # Fallback to project root for backwards compatibility

        real_path = None

        for search_path in search_paths:
            candidate_path = os.path.join(search_path, file_path)
            candidate_real_path = os.path.realpath(candidate_path)

            # Security check: ensure the path is within the project directory
            if candidate_real_path.startswith(project_path) and os.path.exists(candidate_real_path):
                if candidate_real_path.endswith('.md'):
                    real_path = candidate_real_path
                    break

        if not real_path:
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(real_path, 'r') as f:
            return f.read()

    def _generate_virtual_page_content(self, project_name, file_path):
        """
        Generate content for virtual database-driven pages.

        Args:
            project_name: Name of the project
            file_path: Virtual file path

        Returns:
            str: Generated markdown content from database
        """
        from ..models.health import HealthMetric
        from ..models.workout import WorkoutSession
        from ..models.nutrition import MealLog
        from ..models.coaching import CoachingSession, ProgressPhoto
        from flask import current_app
        from flask_login import current_user

        # Map virtual pages to content generators
        if file_path == 'data/health-metrics-log.md':
            return self._generate_health_metrics_log()
        elif file_path == 'data/workout-log.md':
            return self._generate_workout_log()
        elif file_path == 'data/meal-log.md':
            return self._generate_meal_log()
        elif file_path == 'data/progress-photos.md':
            return self._generate_progress_photos()
        elif file_path == 'data/coaching-sessions.md':
            return self._generate_coaching_sessions()
        else:
            raise FileNotFoundError(f"Unknown virtual page: {file_path}")

    def _generate_health_metrics_log(self):
        """Generate health metrics log from database"""
        from ..models.health import HealthMetric
        from flask_login import current_user

        if not current_user.is_authenticated:
            return "# Health Metrics Log\n\n*Please log in to view your health metrics.*"

        metrics = HealthMetric.query.filter_by(user_id=current_user.id).order_by(HealthMetric.recorded_date.desc()).all()

        content = "# Health Metrics Log\n\n"
        content += "Track your weight, body fat percentage, and other health metrics over time.\n\n"

        if not metrics:
            content += "*No health metrics recorded yet.*\n"
            return content

        content += "| Date | Weight (lbs) | Body Fat % | BMI | Notes |\n"
        content += "|------|--------------|------------|-----|-------|\n"

        for metric in metrics:
            date = metric.recorded_date.strftime('%Y-%m-%d')
            weight = f"{metric.weight:.1f}" if metric.weight else "—"
            bodyfat = f"{metric.body_fat_percentage:.1f}" if metric.body_fat_percentage else "—"
            bmi = f"{metric.bmi:.1f}" if metric.bmi else "—"
            notes = metric.notes or ""
            content += f"| {date} | {weight} | {bodyfat} | {bmi} | {notes} |\n"

        return content

    def _generate_workout_log(self):
        """Generate workout log from database"""
        from ..models.workout import WorkoutSession
        from flask_login import current_user

        if not current_user.is_authenticated:
            return "# Workout Log\n\n*Please log in to view your workout history.*"

        workouts = WorkoutSession.query.filter_by(user_id=current_user.id).order_by(WorkoutSession.session_date.desc()).limit(50).all()

        content = "# Workout Log\n\n"
        content += "Recent workout sessions and exercise tracking.\n\n"

        if not workouts:
            content += "*No workouts recorded yet.*\n"
            return content

        for workout in workouts:
            date = workout.session_date.strftime('%Y-%m-%d')
            content += f"\n## {date} - {workout.workout_type or 'Workout'}\n\n"
            if workout.duration_minutes:
                content += f"**Duration:** {workout.duration_minutes} minutes\n\n"
            if workout.notes:
                content += f"{workout.notes}\n\n"

            if workout.exercises:
                content += "### Exercises\n\n"
                for exercise in workout.exercises:
                    content += f"- **{exercise.exercise_name}**: {exercise.sets} sets × {exercise.reps} reps"
                    if exercise.weight:
                        content += f" @ {exercise.weight} lbs"
                    content += "\n"

        return content

    def _generate_meal_log(self):
        """Generate meal log from database"""
        from ..models.nutrition import MealLog
        from flask_login import current_user

        if not current_user.is_authenticated:
            return "# Meal Log\n\n*Please log in to view your meal history.*"

        meals = MealLog.query.filter_by(user_id=current_user.id).order_by(MealLog.meal_date.desc()).limit(30).all()

        content = "# Meal Log\n\n"
        content += "Daily nutrition tracking and meal records.\n\n"

        if not meals:
            content += "*No meals recorded yet.*\n"
            return content

        current_date = None
        for meal in meals:
            date = meal.meal_date.strftime('%Y-%m-%d')
            if date != current_date:
                content += f"\n## {date}\n\n"
                current_date = date

            content += f"### {meal.meal_type.value.title()}\n\n"
            if meal.description:
                content += f"{meal.description}\n\n"
            if meal.calories or meal.protein_g or meal.carbs_g or meal.fat_g:
                content += "**Macros:** "
                parts = []
                if meal.calories:
                    parts.append(f"{meal.calories} cal")
                if meal.protein_g:
                    parts.append(f"{meal.protein_g}g protein")
                if meal.carbs_g:
                    parts.append(f"{meal.carbs_g}g carbs")
                if meal.fat_g:
                    parts.append(f"{meal.fat_g}g fat")
                content += " | ".join(parts) + "\n\n"

        return content

    def _generate_progress_photos(self):
        """Generate progress photos page from database"""
        from ..models.coaching import ProgressPhoto
        from flask_login import current_user

        if not current_user.is_authenticated:
            return "# Progress Photos\n\n*Please log in to view your progress photos.*"

        photos = ProgressPhoto.query.filter_by(user_id=current_user.id).order_by(ProgressPhoto.photo_date.desc()).all()

        content = "# Progress Photos\n\n"
        content += "Visual tracking of your transformation journey.\n\n"

        if not photos:
            content += "*No progress photos uploaded yet.*\n"
            return content

        for photo in photos:
            date = photo.photo_date.strftime('%Y-%m-%d')
            content += f"## {date}\n\n"
            if photo.photo_url:
                content += f"![Progress Photo]({photo.photo_url})\n\n"
            if photo.notes:
                content += f"{photo.notes}\n\n"
            content += "---\n\n"

        return content

    def _generate_coaching_sessions(self):
        """Generate coaching sessions log from database"""
        from ..models.coaching import CoachingSession
        from flask_login import current_user

        if not current_user.is_authenticated:
            return "# Coaching Sessions\n\n*Please log in to view your coaching sessions.*"

        sessions = CoachingSession.query.filter_by(user_id=current_user.id).order_by(CoachingSession.session_date.desc()).all()

        content = "# Coaching Sessions\n\n"
        content += "Record of coaching feedback, plans, and progress discussions.\n\n"

        if not sessions:
            content += "*No coaching sessions recorded yet.*\n"
            return content

        for session in sessions:
            date = session.session_date.strftime('%Y-%m-%d')
            content += f"\n## {date}\n\n"
            if session.session_type:
                content += f"**Type:** {session.session_type}\n\n"
            if session.notes:
                content += f"{session.notes}\n\n"
            if session.action_items:
                content += "### Action Items\n\n"
                content += f"{session.action_items}\n\n"
            content += "---\n\n"

        return content

    def get_gemini_file(self, project_name):
        """Get GEMINI.md file content for a project"""
        if project_name not in self.project_dirs:
            raise ValueError(f"Project '{project_name}' not found")

        gemini_path = os.path.join(self.project_root, project_name, 'GEMINI.md')

        if not os.path.exists(gemini_path):
            raise FileNotFoundError(f"GEMINI.md not found for {project_name}")

        with open(gemini_path, 'r') as f:
            return f.read()


class FileCategorizer:
    """Categorizes markdown files based on content analysis"""

    # Keywords that indicate file categories
    CATEGORY_KEYWORDS = {
        'nutrition': [
            'meal', 'diet', 'food', 'eating', 'nutrition', 'recipe', 'shopping',
            'calorie', 'protein', 'carb', 'fat', 'vitamin', 'supplement',
            'breakfast', 'lunch', 'dinner', 'snack', 'grocery'
        ],
        'training': [
            'workout', 'exercise', 'training', 'fitness', 'gym', 'strength',
            'cardio', 'resistance', 'muscle', 'progressive', 'overload',
            'sets', 'reps', 'routine', 'martial', 'roadmap'
        ],
        'tracking': [
            'log', 'track', 'metric', 'progress', 'check-in', 'checkin',
            'weight', 'body fat', 'measurement', 'graph', 'chart', 'data'
        ],
        'learning': [
            'curriculum', 'course', 'lesson', 'tutorial', 'guide', 'learn',
            'study', 'education', 'skill', 'training', 'week', 'module'
        ],
        'reference': [
            'reference', 'documentation', 'api', 'persona', 'template',
            'example', 'sample', 'index', 'glossary'
        ],
        'narrative': [
            'story', 'journey', 'origin', 'about', 'brand', 'vision',
            'mission', 'philosophy', 'narrative', 'developer'
        ],
        'coaching': [
            'coaching', 'session', 'feedback', 'review', 'plan', 'strategy',
            'goal', 'advice', 'recommendation'
        ]
    }

    # Default categories for each project type
    PROJECT_CATEGORY_ORDER = {
        'Health_and_Fitness': ['training', 'nutrition', 'tracking', 'coaching', 'reference'],
        'AI_Development': ['learning', 'narrative', 'reference', 'coaching']
    }

    @classmethod
    def categorize_file(cls, filename, content=None):
        """
        Categorize a file based on filename and optionally content.

        Args:
            filename: Name of the file
            content: Optional file content for deeper analysis

        Returns:
            str: Category name
        """
        filename_lower = filename.lower()

        # Check filename first
        for category, keywords in cls.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return category

        # If content provided, analyze it
        if content:
            content_lower = content[:2000].lower()  # Only check first 2000 chars
            category_scores = {}

            for category, keywords in cls.CATEGORY_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw in content_lower)
                if score > 0:
                    category_scores[category] = score

            if category_scores:
                return max(category_scores, key=category_scores.get)

        return 'general'

    @classmethod
    def categorize_project_files(cls, project_name, files_with_content):
        """
        Categorize all files in a project.

        Args:
            project_name: Name of the project
            files_with_content: List of tuples (filename, content)

        Returns:
            dict: Category -> list of files mapping
        """
        categorized = {}

        for filename, content in files_with_content:
            category = cls.categorize_file(filename, content)
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(filename)

        # Sort categories based on project preference
        category_order = cls.PROJECT_CATEGORY_ORDER.get(project_name, [])
        sorted_categories = {}

        # Add categories in preferred order first
        for cat in category_order:
            if cat in categorized:
                sorted_categories[cat] = sorted(categorized[cat])

        # Add remaining categories
        for cat in sorted(categorized.keys()):
            if cat not in sorted_categories:
                sorted_categories[cat] = sorted(categorized[cat])

        return sorted_categories

    @classmethod
    def get_category_display_name(cls, category):
        """Get a human-readable display name for a category"""
        display_names = {
            'nutrition': 'Nutrition',
            'training': 'Training',
            'tracking': 'Tracking & Metrics',
            'learning': 'Learning',
            'reference': 'Reference',
            'narrative': 'Story & Vision',
            'coaching': 'Coaching',
            'general': 'Documents'
        }
        return display_names.get(category, category.title())


class HealthDataParser:
    """Parses health data from markdown tables"""

    @staticmethod
    def parse_health_data(filepath):
        """
        Parse weight and body fat data from check-in-log.md

        Returns:
            dict: Weight and body fat data
        """
        if not os.path.exists(filepath):
            return {'weight': [], 'bodyfat': []}

        weight_data = []
        bodyfat_data = []

        with open(filepath, 'r') as f:
            lines = f.readlines()
            # Skip header and separator
            for line in lines[2:]:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 3:
                    date = parts[0]
                    weight = parts[1]
                    bodyfat = parts[2]

                    if weight != 'None':
                        try:
                            weight_data.append({'x': date, 'y': float(weight)})
                        except ValueError:
                            pass

                    if bodyfat != 'None':
                        try:
                            bodyfat_data.append({'x': date, 'y': float(bodyfat)})
                        except ValueError:
                            pass

        return {'weight': weight_data, 'bodyfat': bodyfat_data}
