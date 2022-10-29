from django.core.paginator import Paginator
from django.conf import settings

from posts.models import Post


def post_paginator(queryset, request, requ_fl = True):
    if requ_fl: 
        if request == 'index':
            paginator = Paginator(queryset, settings.POSTS_PER_PAGE)
            page_number = 1
            page_obj = paginator.get_page(page_number)
        else:
            paginator = Paginator(queryset, settings.POSTS_PER_PAGE)
        
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
    else: 
        paginator = Paginator(queryset, settings.POSTS_PER_PAGE)
        if Post.objects.all().count()%settings.POSTS_PER_PAGE == 0:
            page_number = Post.objects.all().count()//settings.POSTS_PER_PAGE
        else:
            page_number = Post.objects.all().count()//settings.POSTS_PER_PAGE + 1
        page_obj = paginator.get_page(page_number)
    return page_obj
