"""
Custom pagination classes for optimized API responses
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class OptimizedPagination(PageNumberPagination):
    """Optimized pagination with configurable page size"""

    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'data': data,
            'pagination': {
                'count': self.page.paginator.count,
                'page': self.page.number,
                'pages': self.page.paginator.num_pages,
                'page_size': self.get_page_size(self.request),
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
            }
        })


class SmallResultsPagination(PageNumberPagination):
    """Small page size for quick responses"""
    page_size = 10
    max_page_size = 50


class LargeResultsPagination(PageNumberPagination):
    """Larger page size for bulk operations"""
    page_size = 50
    max_page_size = 200
