"""
Document API
============

RESTful API endpoints for document management.

Endpoints:
- Document CRUD operations
- Document search and filtering
- Document type listing
"""

import logging
from datetime import datetime, timezone
from flask import Blueprint, request
from flask_login import current_user
from sqlalchemy import or_

from .. import db, csrf
from ..models.document import Document, DocumentType
from . import (
    success_response,
    error_response,
    paginated_response,
    require_active_user,
    validate_request_data,
    validate_pagination_params
)

# Create blueprint
document_api_bp = Blueprint('document_api', __name__, url_prefix='/document')

# Configure logger
logger = logging.getLogger(__name__)


# ====================================================================================
# Document CRUD Endpoints
# ====================================================================================

@document_api_bp.route('/', methods=['GET'])
@require_active_user
def list_documents():
    """
    Get list of user's documents with filtering and pagination.

    Query Parameters:
        - document_type (str): Filter by document type
        - tags (str): Filter by tags (comma-separated)
        - include_archived (bool): Include archived documents (default: false)
        - include_content (bool): Include full content (default: false)
        - page (int): Page number (default: 1)
        - per_page (int): Items per page (default: 20, max: 100)
        - sort (str): Sort order 'asc' or 'desc' (default: desc)

    Returns:
        Paginated list of documents
    """
    try:
        # Get pagination params (returns tuple)
        page, per_page = validate_pagination_params()

        # Get filter params
        document_type = request.args.get('document_type')
        tags_param = request.args.get('tags')
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        include_content = request.args.get('include_content', 'false').lower() == 'true'
        sort = request.args.get('sort', 'desc').lower()

        # Build query
        query = Document.query.filter_by(user_id=current_user.id)

        # Filter by archived status
        if not include_archived:
            query = query.filter_by(is_archived=False)

        # Filter by document type
        if document_type:
            try:
                doc_type = DocumentType(document_type)
                query = query.filter_by(document_type=doc_type)
            except ValueError:
                return error_response(f"Invalid document type: {document_type}", status_code=400)

        # Filter by tags
        if tags_param:
            tags = [t.strip() for t in tags_param.split(',')]
            query = query.filter(Document.tags.overlap(tags))

        # Apply sorting
        if sort == 'asc':
            query = query.order_by(Document.created_at.asc())
        else:
            query = query.order_by(Document.created_at.desc())

        # Execute paginated query
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        # Serialize documents
        documents = [doc.to_dict(include_content=include_content) for doc in paginated.items]

        return paginated_response(
            items=documents,
            page=paginated.page,
            per_page=paginated.per_page,
            total=paginated.total
        )

    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        return error_response('Failed to list documents', status_code=500)


@document_api_bp.route('/', methods=['POST'])
@csrf.exempt
@require_active_user
def create_document():
    """
    Create a new document.

    Request Body:
        {
            "title": "My Workout Plan",
            "document_type": "workout_plan",
            "content": "# Week 1...",
            "summary": "12-week strength program",
            "tags": ["strength", "beginner"],
            "metadata": {"duration_weeks": 12},
            "source": "ai_coach",
            "conversation_id": 123
        }

    Returns:
        Created document data
    """
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided', status_code=400)

        # Validate required fields
        required_fields = ['title', 'document_type', 'content']
        validation = validate_request_data(data, required_fields)
        if validation:
            return validation

        # Validate document type
        try:
            doc_type = DocumentType(data['document_type'])
        except ValueError:
            valid_types = [dt.value for dt in DocumentType]
            return error_response(f"Invalid document type. Valid types: {valid_types}", status_code=400)

        # Get existing slugs for collision detection
        existing_slugs = [d.slug for d in Document.query.filter_by(user_id=current_user.id).all()]

        # Generate slug
        slug = Document.generate_slug(data['title'], current_user.id, existing_slugs)

        # Create document
        document = Document(
            user_id=current_user.id,
            title=data['title'].strip(),
            slug=slug,
            document_type=doc_type,
            content=data['content'],
            summary=data.get('summary', '')[:500] if data.get('summary') else None,
            metadata_json=data.get('metadata', {}),
            tags=data.get('tags', []),
            source=data.get('source', 'manual'),
            conversation_id=data.get('conversation_id'),
            is_public=data.get('is_public', False),
            is_archived=False
        )

        db.session.add(document)
        db.session.commit()

        logger.info(f"Document created: {document.id} for user {current_user.id}")

        return success_response(document.to_dict(), status_code=201)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating document: {e}", exc_info=True)
        return error_response('Failed to create document', status_code=500)


@document_api_bp.route('/<int:document_id>', methods=['GET'])
@require_active_user
def get_document(document_id: int):
    """
    Get a specific document by ID.

    Path Parameters:
        - document_id: Document ID

    Returns:
        Document data with full content
    """
    try:
        document = Document.query.filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()

        if not document:
            return error_response('Document not found', status_code=404)

        return success_response(document.to_dict(include_content=True))

    except Exception as e:
        logger.error(f"Error fetching document {document_id}: {e}", exc_info=True)
        return error_response('Failed to fetch document', status_code=500)


@document_api_bp.route('/slug/<slug>', methods=['GET'])
@require_active_user
def get_document_by_slug(slug: str):
    """
    Get a specific document by slug.

    Path Parameters:
        - slug: Document slug

    Returns:
        Document data with full content
    """
    try:
        document = Document.query.filter_by(
            slug=slug,
            user_id=current_user.id
        ).first()

        if not document:
            return error_response('Document not found', status_code=404)

        return success_response(document.to_dict(include_content=True))

    except Exception as e:
        logger.error(f"Error fetching document by slug {slug}: {e}", exc_info=True)
        return error_response('Failed to fetch document', status_code=500)


@document_api_bp.route('/<int:document_id>', methods=['PUT'])
@csrf.exempt
@require_active_user
def update_document(document_id: int):
    """
    Update an existing document.

    Path Parameters:
        - document_id: Document ID

    Request Body:
        {
            "title": "Updated Title",
            "content": "# Updated content...",
            "summary": "Updated summary",
            "tags": ["tag1", "tag2"],
            "metadata": {},
            "is_public": false
        }

    Returns:
        Updated document data
    """
    try:
        document = Document.query.filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()

        if not document:
            return error_response('Document not found', status_code=404)

        data = request.get_json()
        if not data:
            return error_response('No data provided', status_code=400)

        # Update fields if provided
        if 'title' in data:
            document.title = data['title'].strip()
            # Regenerate slug if title changed
            existing_slugs = [d.slug for d in Document.query.filter(
                Document.user_id == current_user.id,
                Document.id != document_id
            ).all()]
            document.slug = Document.generate_slug(data['title'], current_user.id, existing_slugs)

        if 'content' in data:
            document.content = data['content']

        if 'summary' in data:
            document.summary = data['summary'][:500] if data['summary'] else None

        if 'tags' in data:
            document.tags = data['tags']

        if 'metadata' in data:
            document.metadata_json = data['metadata']

        if 'is_public' in data:
            document.is_public = bool(data['is_public'])

        if 'document_type' in data:
            try:
                document.document_type = DocumentType(data['document_type'])
            except ValueError:
                return error_response(f"Invalid document type: {data['document_type']}", status_code=400)

        db.session.commit()

        logger.info(f"Document updated: {document.id}")

        return success_response(document.to_dict())

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating document {document_id}: {e}", exc_info=True)
        return error_response('Failed to update document', status_code=500)


@document_api_bp.route('/<int:document_id>', methods=['DELETE'])
@csrf.exempt
@require_active_user
def delete_document(document_id: int):
    """
    Soft delete (archive) a document.

    Path Parameters:
        - document_id: Document ID

    Query Parameters:
        - permanent (bool): Permanently delete instead of archive (default: false)

    Returns:
        Success message
    """
    try:
        document = Document.query.filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()

        if not document:
            return error_response('Document not found', status_code=404)

        permanent = request.args.get('permanent', 'false').lower() == 'true'

        if permanent:
            db.session.delete(document)
            db.session.commit()
            logger.info(f"Document permanently deleted: {document_id}")
            return success_response({'message': 'Document permanently deleted'})
        else:
            document.is_archived = True
            db.session.commit()
            logger.info(f"Document archived: {document_id}")
            return success_response({'message': 'Document archived'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting document {document_id}: {e}", exc_info=True)
        return error_response('Failed to delete document', status_code=500)


@document_api_bp.route('/<int:document_id>/restore', methods=['POST'])
@csrf.exempt
@require_active_user
def restore_document(document_id: int):
    """
    Restore an archived document.

    Path Parameters:
        - document_id: Document ID

    Returns:
        Restored document data
    """
    try:
        document = Document.query.filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()

        if not document:
            return error_response('Document not found', status_code=404)

        document.is_archived = False
        db.session.commit()

        logger.info(f"Document restored: {document_id}")

        return success_response(document.to_dict())

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error restoring document {document_id}: {e}", exc_info=True)
        return error_response('Failed to restore document', status_code=500)


# ====================================================================================
# Search and Utility Endpoints
# ====================================================================================

@document_api_bp.route('/search', methods=['GET'])
@require_active_user
def search_documents():
    """
    Search documents by title or content.

    Query Parameters:
        - q (str): Search query (required)
        - document_type (str): Filter by document type
        - include_archived (bool): Include archived documents (default: false)
        - limit (int): Maximum results (default: 20, max: 50)

    Returns:
        List of matching documents (without full content)
    """
    try:
        query_text = request.args.get('q', '').strip()
        if not query_text:
            return error_response('Search query is required', status_code=400)

        document_type = request.args.get('document_type')
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        limit = min(int(request.args.get('limit', 20)), 50)

        # Build search query
        search_pattern = f'%{query_text}%'
        query = Document.query.filter(
            Document.user_id == current_user.id,
            or_(
                Document.title.ilike(search_pattern),
                Document.content.ilike(search_pattern),
                Document.summary.ilike(search_pattern)
            )
        )

        if not include_archived:
            query = query.filter_by(is_archived=False)

        if document_type:
            try:
                doc_type = DocumentType(document_type)
                query = query.filter_by(document_type=doc_type)
            except ValueError:
                pass  # Ignore invalid type in search

        # Order by relevance (title matches first) and recency
        documents = query.order_by(Document.updated_at.desc()).limit(limit).all()

        # Return without full content for faster response
        results = [doc.to_dict(include_content=False) for doc in documents]

        return success_response(results)

    except Exception as e:
        logger.error(f"Error searching documents: {e}", exc_info=True)
        return error_response('Failed to search documents', status_code=500)


@document_api_bp.route('/types', methods=['GET'])
@require_active_user
def get_document_types():
    """
    Get list of available document types.

    Returns:
        List of document type choices
    """
    try:
        types = Document.get_type_choices()
        return success_response(types)

    except Exception as e:
        logger.error(f"Error fetching document types: {e}", exc_info=True)
        return error_response('Failed to fetch document types', status_code=500)


@document_api_bp.route('/recent', methods=['GET'])
@require_active_user
def get_recent_documents():
    """
    Get user's most recent documents.

    Query Parameters:
        - limit (int): Number of documents (default: 5, max: 20)

    Returns:
        List of recent documents without full content
    """
    try:
        limit = min(int(request.args.get('limit', 5)), 20)

        documents = Document.query.filter_by(
            user_id=current_user.id,
            is_archived=False
        ).order_by(
            Document.updated_at.desc()
        ).limit(limit).all()

        results = [doc.to_dict(include_content=False) for doc in documents]

        return success_response(results)

    except Exception as e:
        logger.error(f"Error fetching recent documents: {e}", exc_info=True)
        return error_response('Failed to fetch recent documents', status_code=500)
