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

    def __init__(self, project_root, project_dirs, allow_data_access=False):
        self.project_root = project_root
        self.project_dirs = project_dirs
        self.allow_data_access = allow_data_access

    def get_project_files(self, project_name, file_order=None):
        """
        Get all markdown files for a project.

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

        # Apply custom ordering if provided
        if file_order:
            markdown_files.sort(key=lambda f: (
                file_order.index(f) if f in file_order else len(file_order)
            ))

        return markdown_files

    def get_file_content(self, project_name, file_path):
        """
        Get content of a specific file.

        Args:
            project_name: Name of the project
            file_path: Path to the file within the docs/ subdirectory (or data/ if allow_data_access=True)

        Returns:
            str: File content
        """
        if project_name not in self.project_dirs:
            raise ValueError(f"Project '{project_name}' not found")

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
