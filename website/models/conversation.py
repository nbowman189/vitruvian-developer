"""
Conversation Log Model
======================

Stores AI coaching conversation history with the Gemini AI coach.
Each conversation contains a JSON array of messages exchanged between user and AI.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean, JSON, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db


class ConversationLog(db.Model):
    """
    AI coaching conversation log model.

    Stores full conversation history between user and AI coach (Gemini).
    Messages are stored as JSON array with role, content, and timestamp.
    Supports record tracking to count how many database records were created from conversation.
    """

    __tablename__ = 'conversation_logs'

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Conversation Metadata
    conversation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        default=lambda: datetime.now(timezone.utc)
    )
    title: Mapped[Optional[str]] = mapped_column(String(200))  # Auto-generated or user-set

    # Message Data
    messages: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: []
    )
    message_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # Activity Tracking
    records_created: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    user = relationship('User', back_populates='conversation_logs')
    documents = relationship('Document', back_populates='conversation')

    # Table Constraints
    __table_args__ = (
        CheckConstraint('message_count >= 0', name='check_message_count_positive'),
        CheckConstraint('records_created >= 0', name='check_records_created_positive'),
        Index('ix_conversation_logs_user_date', 'user_id', 'conversation_date'),
        Index('ix_conversation_logs_user_active', 'user_id', 'is_active'),
    )

    def __repr__(self) -> str:
        return f'<ConversationLog id={self.id} user_id={self.user_id} messages={self.message_count}>'

    # Message Management
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a message to the conversation.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata (e.g., function_call, record_type)
        """
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        if metadata:
            message['metadata'] = metadata

        # Initialize messages list if None
        if self.messages is None:
            self.messages = []

        self.messages.append(message)
        self.message_count = len(self.messages)
        self.last_message_at = datetime.now(timezone.utc)

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent N messages from conversation.

        Args:
            limit: Maximum number of messages to return (default: 10)

        Returns:
            List of message dictionaries
        """
        if not self.messages:
            return []
        return self.messages[-limit:]

    def increment_records_created(self) -> None:
        """Increment the count of database records created from this conversation."""
        self.records_created += 1

    def generate_title(self) -> str:
        """
        Auto-generate conversation title from first user message.

        Returns:
            Title string (truncated to 50 chars)
        """
        if not self.messages:
            return "New Conversation"

        # Find first user message
        for message in self.messages:
            if message.get('role') == 'user':
                content = message.get('content', '')
                # Truncate to 50 chars and add ellipsis if needed
                if len(content) > 50:
                    return content[:47] + '...'
                return content if content else "New Conversation"

        return "New Conversation"

    def mark_inactive(self) -> None:
        """Mark conversation as inactive (archived)."""
        self.is_active = False

    def mark_active(self) -> None:
        """Mark conversation as active."""
        self.is_active = True

    # Serialization
    def to_dict(self, include_messages: bool = True) -> dict:
        """
        Convert conversation to dictionary for API responses.

        Args:
            include_messages: Include full message history (default: True)

        Returns:
            Dictionary representation of conversation
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'conversation_date': self.conversation_date.isoformat() if self.conversation_date else None,
            'title': self.title or self.generate_title(),
            'message_count': self.message_count,
            'records_created': self.records_created,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
        }

        if include_messages:
            data['messages'] = self.messages or []

        return data

    def to_summary_dict(self) -> dict:
        """
        Convert conversation to summary dictionary (without full messages).

        Returns:
            Dictionary with conversation metadata only
        """
        return self.to_dict(include_messages=False)
