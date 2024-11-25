from math import ceil
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class Pagination(PageNumberPagination):
    page_size = 25  
    page_size_query_param = 'page_size'  
    max_page_size = 50  

    def get_paginated_response(self, data):
        """
        Custom response pagination
        """
        total = self.page.paginator.count  
        page_size = self.page.paginator.per_page  
        total_pages = ceil(total / page_size)
        page = self.page.number
        return Response({
            'success': True,
            'message': 'successful',
            'data': data,
            'pagination': {
                'total': total,  
                'page': page,  
                'page_size': page_size,
                'total_pages': total_pages,
                'next': self.get_next_link(),  
                'previous': self.get_previous_link()  
            }
        })
