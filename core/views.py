from django.shortcuts import render
from rest_framework.pagination import PageNumberPagination
# Create your views here.



class PaginationClass(PageNumberPagination):
    page_size = 10  # Set the number of items you want per page
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    
    