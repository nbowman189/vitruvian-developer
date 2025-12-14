"""
Pagination utilities for handling large datasets
"""

from typing import List, TypeVar, Generic, Dict, Any
from math import ceil


T = TypeVar('T')


class Paginator(Generic[T]):
    """Generic paginator for any list-like data"""

    def __init__(self, items: List[T], per_page: int = 10, page: int = 1):
        """
        Initialize paginator

        Args:
            items: List of items to paginate
            per_page: Number of items per page
            page: Current page number (1-indexed)
        """
        self.items = items
        self.per_page = max(1, per_page)  # Ensure at least 1
        self.page = max(1, page)  # Ensure at least page 1
        self.total = len(items)

    @property
    def pages(self) -> int:
        """Get total number of pages"""
        return ceil(self.total / self.per_page)

    @property
    def has_prev(self) -> bool:
        """Check if there is a previous page"""
        return self.page > 1

    @property
    def has_next(self) -> bool:
        """Check if there is a next page"""
        return self.page < self.pages

    @property
    def prev_num(self) -> int:
        """Get previous page number"""
        return self.page - 1 if self.has_prev else None

    @property
    def next_num(self) -> int:
        """Get next page number"""
        return self.page + 1 if self.has_next else None

    @property
    def items_per_page(self) -> List[T]:
        """Get items for current page"""
        if self.page > self.pages and self.total > 0:
            return []

        start = (self.page - 1) * self.per_page
        end = start + self.per_page
        return self.items[start:end]

    def iter_pages(self, left_edge=1, left_current=1, right_current=2, right_edge=1):
        """
        Iterate page numbers for pagination display

        Args:
            left_edge: Pages shown at left edge
            left_current: Pages shown left of current
            right_current: Pages shown right of current
            right_edge: Pages shown at right edge

        Yields:
            Page numbers or None for gaps
        """
        last = 0

        for num in self.get_page_range(left_edge, left_current, right_current, right_edge):
            if num is None:
                if last + 1 != 0:
                    yield None
                    last = 0
            else:
                if last + 1 != num:
                    yield None
                yield num
                last = num

    def get_page_range(self, left_edge, left_current, right_current, right_edge):
        """Get range of pages to display"""
        if self.pages <= left_edge + right_edge + left_current + right_current + 2:
            return range(1, self.pages + 1)

        result = list(range(1, left_edge + 1))

        left_threshold = self.page - left_current
        if left_threshold > left_edge + 1:
            result.append(None)
        result.extend(range(max(left_edge + 1, left_threshold), self.page + 1))

        right_threshold = self.page + right_current
        result.extend(range(self.page + 1, min(self.pages - right_edge, right_threshold) + 1))

        if right_threshold < self.pages - right_edge:
            result.append(None)
        result.extend(range(max(self.pages - right_edge + 1, right_threshold + 1), self.pages + 1))

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert paginator to dictionary"""
        return {
            'page': self.page,
            'per_page': self.per_page,
            'total': self.total,
            'pages': self.pages,
            'has_prev': self.has_prev,
            'has_next': self.has_next,
            'prev_num': self.prev_num,
            'next_num': self.next_num,
            'items': self.items_per_page
        }


def paginate_response(items: List[Any], page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    """
    Create paginated response

    Args:
        items: List of items
        page: Current page number
        per_page: Items per page

    Returns:
        Paginated response dictionary
    """
    paginator = Paginator(items, per_page=per_page, page=page)
    return paginator.to_dict()


def validate_pagination_params(page: int = 1, per_page: int = 10) -> tuple:
    """
    Validate and sanitize pagination parameters

    Args:
        page: Page number
        per_page: Items per page

    Returns:
        Tuple of (page, per_page) with valid values
    """
    try:
        page = int(page) if isinstance(page, (int, str)) else 1
        page = max(1, page)
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = int(per_page) if isinstance(per_page, (int, str)) else 10
        per_page = max(1, min(100, per_page))
    except (ValueError, TypeError):
        per_page = 10

    return page, per_page
