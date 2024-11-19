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
        return Response({
            'success': True,
            'message': 'Pagination successful',
            'data': data,
            'pagination': {
                'count': self.page.paginator.count,  
                'page': self.page.number,  
                'page_size': self.page.paginator.per_page,  
                'next': self.get_next_link(),  
                'previous': self.get_previous_link()  
            }
        })
