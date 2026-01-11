"""
Document Model
==============

Stores AI-generated and user-created documents like workout plans,
meal plans, progress reports, and fitness roadmaps.
"""

import enum
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Boolean, Enum, Index, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
import re

from . import db


class DocumentType(enum.Enum):
    """Types of documents that can be created and stored."""
    WORKOUT_PLAN = 'workout_plan'
    MEAL_PLAN = 'meal_plan'
    PROGRESS_REPORT = 'progress_report'
    FITNESS_ROADMAP = 'fitness_roadmap'
    ANALYSIS = 'analysis'
    COACHING_NOTES = 'coaching_notes'
    EDUCATIONAL = 'educational'
    CUSTOM = 'custom'


class Document(db.Model):
    """
    Document storage model.

    Stores markdown documents created by the AI coach or manually by users.
    Supports various document types with metadata for type-specific data.
    """

    __tablename__ = 'documents'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    conversation_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('conversation_logs.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )

    # Document Identity
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(300), nullable=False)

    # Document Type
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType),
        nullable=False,
        default=DocumentType.CUSTOM
    )

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Metadata and Tags
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    tags: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(50)),
        nullable=True,
        default=list
    )

    # Status Flags
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Source Tracking
    source: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default='manual'
    )  # 'ai_coach', 'manual', 'import'

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user = relationship('User', back_populates='documents')
    conversation = relationship('ConversationLog', back_populates='documents')

    # Table Constraints
    __table_args__ = (
        Index('ix_documents_user_slug', 'user_id', 'slug', unique=True),
        Index('ix_documents_user_type', 'user_id', 'document_type'),
        Index('ix_documents_user_archived', 'user_id', 'is_archived'),
    )

    def __repr__(self) -> str:
        return f'<Document id={self.id} title="{self.title}" type={self.document_type.value}>'

    @staticmethod
    def generate_slug(title: str, user_id: int, existing_slugs: List[str] = None) -> str:
        """
        Generate a URL-friendly slug from the title.

        Args:
            title: Document title
            user_id: User ID (for uniqueness check)
            existing_slugs: List of existing slugs to avoid collisions

        Returns:
            Unique slug string
        """
        # Convert to lowercase and replace spaces with hyphens
        slug = title.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special characters
        slug = re.sub(r'[-\s]+', '-', slug)  # Replace spaces and multiple hyphens
        slug = slug.strip('-')  # Remove leading/trailing hyphens

        # Truncate to reasonable length
        if len(slug) > 250:
            slug = slug[:250].rsplit('-', 1)[0]

        # Handle collisions
        if existing_slugs:
            base_slug = slug
            counter = 1
            while slug in existing_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1

        return slug

    @property
    def document_type_display(self) -> str:
        """Human-readable document type."""
        type_labels = {
            DocumentType.WORKOUT_PLAN: 'Workout Plan',
            DocumentType.MEAL_PLAN: 'Meal Plan',
            DocumentType.PROGRESS_REPORT: 'Progress Report',
            DocumentType.FITNESS_ROADMAP: 'Fitness Roadmap',
            DocumentType.ANALYSIS: 'Analysis',
            DocumentType.COACHING_NOTES: 'Coaching Notes',
            DocumentType.EDUCATIONAL: 'Educational',
            DocumentType.CUSTOM: 'Custom',
        }
        return type_labels.get(self.document_type, 'Document')

    @property
    def source_display(self) -> str:
        """Human-readable source."""
        source_labels = {
            'ai_coach': 'AI Coach',
            'manual': 'Manual',
            'import': 'Imported',
        }
        return source_labels.get(self.source, 'Unknown')

    def to_dict(self, include_content: bool = True) -> dict:
        """
        Convert document to dictionary for API responses.

        Args:
            include_content: Include full content (default: True).
                             Set to False for list views.

        Returns:
            Dictionary representation of document
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'slug': self.slug,
            'document_type': self.document_type.value,
            'document_type_display': self.document_type_display,
            'summary': self.summary,
            'metadata': self.metadata_json,
            'tags': self.tags or [],
            'is_public': self.is_public,
            'is_archived': self.is_archived,
            'source': self.source,
            'source_display': self.source_display,
            'conversation_id': self.conversation_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_content:
            data['content'] = self.content

        return data

    @classmethod
    def get_type_choices(cls) -> List[dict]:
        """Return list of document type choices for forms/API."""
        return [
            {'value': dt.value, 'label': cls._type_label(dt)}
            for dt in DocumentType
        ]

    @staticmethod
    def _type_label(doc_type: DocumentType) -> str:
        """Get label for document type."""
        labels = {
            DocumentType.WORKOUT_PLAN: 'Workout Plan',
            DocumentType.MEAL_PLAN: 'Meal Plan',
            DocumentType.PROGRESS_REPORT: 'Progress Report',
            DocumentType.FITNESS_ROADMAP: 'Fitness Roadmap',
            DocumentType.ANALYSIS: 'Analysis',
            DocumentType.COACHING_NOTES: 'Coaching Notes',
            DocumentType.EDUCATIONAL: 'Educational',
            DocumentType.CUSTOM: 'Custom',
        }
        return labels.get(doc_type, doc_type.value)
