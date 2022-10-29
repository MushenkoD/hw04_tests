from django.core.paginator import Paginator
from django.conf import settings

from posts.models import Post

def page_obj_func(queryset, number):
    '''Пришлось написать служебную функцию чтобы не портить
    пагинатор так как функцию реквест не вызвать включенного
    отладочного сервера'''
        paginator = Paginator(queryset, settings.POSTS_PER_PAGE)
        page_number = number
        page_obj = paginator.get_page(page_number)
        return page_obj