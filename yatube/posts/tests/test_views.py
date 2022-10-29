from http import HTTPStatus

from django import forms
from django.urls import reverse
from django.test import TestCase, Client
from django.conf import settings
from django.contrib.auth import get_user_model

from posts.models import Post, Group
from posts.tests.utils import page_obj_func

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """ Создаем тестовую группу и тестовыый экземпляр поста
        и 25 тестовых постов для теста пагинатора."""
        super().setUpClass()
        cls.count_post = settings.POSTS_PER_PAGE * 2 + 5
        cls.post_author = User.objects.create_user(username='test_test')
        cls.not_author = User.objects.create_user(username='test_test2')
        cls.group = Group.objects.create(
            title='test_group title',
            slug='test_group_slug',
            description='test_group description',
        )
        cls.group_other = Group.objects.create(
            title='test_group title other',
            slug='test_group_slug_other',
            description='test_group description other',
        )
        cls.post = Post.objects.create(
            text='Test text test text',
            author=cls.post_author,
            group=cls.group,
        )

        for post_number in range(cls.count_post):
            cls.post = Post.objects.create(
                text='Test text test text',
                author=cls.post_author,
                group=cls.group,)

    def setUp(self):
        """Создаем неавторизованный клиент, cоздаем авторизованный клиент
        и авторизуем пользователя и словарь шаблонов."""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post_author)
        self.templates_page_names = {
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile', kwargs={'username': (
                self.post_author.username)}): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': (
                self.post.pk)}): 'posts/create_post.html',
        }
        self.views_dict = {
            'group_posts': reverse('posts:group_posts',
                                   kwargs={'slug': self.group.slug}
                                   ),
            'index': reverse('posts:index'),
            'profile': reverse('posts:profile', kwargs={'username': (
                self.post_author.username)}),
            'post_detail': reverse('posts:post_detail', args=[self.post.id]),
            'create': reverse('posts:post_create'),
            'edit': reverse('posts:post_edit', kwargs={'post_id': (
                self.post.pk)}),

        }

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = self.templates_page_names
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_posts_index_get_correct_context(self):
        """Шаблоны index сформированы с верным контекстом."""
        page_obj = page_obj_func(Post.objects.all(), 1)
        post_author = self.post_author
        post_text = self.post.text
        view = self.views_dict['index']

        response = self.guest_client.get(view)
        first_object = response.context['page_obj'][0]
        text = first_object.text
        author = first_object.author

        self.assertEqual(text, post_text)
        self.assertEqual(author, post_author)
        self.assertEqual(str(response.context['page_obj']), str(page_obj))

    def test_posts_group_posts_get_correct_context(self):
        """Шаблон group_posts сформированы с верным контекстом."""

        post_group = self.group
        post_text = self.post.text
        page_obj = page_obj_func(post_group.posts.all(), 1)
        view = self.views_dict['group_posts']

        response = self.guest_client.get(view)
        first_object = response.context['page_obj'][0]
        text = first_object.text
        group = first_object.group

        self.assertEqual(text, post_text)
        self.assertEqual(group, post_group)
        self.assertEqual(str(response.context['page_obj']), str(page_obj))

    def test_posts_profile_get_correct_context(self):
        """Шаблон profile сформированы с верным контекстом."""
        post_text = self.post.text
        author = self.post_author
        post = self.post
        count = self.count_post + 1
        page_obj = page_obj_func(author.posts.all(), 1)
        view = self.views_dict['profile']

        response = self.guest_client.get(view)
        first_object = response.context['page_obj'][0]
        count_posts = Post.objects.filter(author=post.author_id).count()
        text = first_object.text
        post_author = first_object.author

        self.assertEqual(post_text, text)
        self.assertEqual(count_posts, count)
        self.assertEqual(post_author, author)
        self.assertEqual(str(response.context['page_obj']), str(page_obj))

    def test_posts_post_detail_get_correct_context(self):
        """Шаблон post_detail сформированы с верным контекстом."""
        post_text = self.post.text
        author = self.post_author
        count = self.count_post + 1
        view = self.views_dict['post_detail']

        response = self.guest_client.get(view)
        first_object = response.context['post']
        count_posts = author.posts.all().count()
        text = first_object.text
        post_author = first_object.author

        self.assertEqual(text, post_text)
        self.assertEqual(count_posts, count)
        self.assertEqual(post_author, author)

    def test_create_post_show_correct_context_create(self):
        """Шаблон create с верным контекстом."""
        view = self.views_dict['create']

        response = self.authorized_client.get(view)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_post_show_correct_context(self):
        """Шаблон edit с верным контекстом."""
        view = self.views_dict['edit']
        postid = self.post.id

        response = self.authorized_client.get(view)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        post_id = response.context['post_id']

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertEqual(post_id, postid)

    def test_post_in_this_group(self):
        """Проверка: пост  группу."""
        group = self.group
        text = self.post.text
        view = self.views_dict['group_posts']

        response = self.authorized_client.get(view)
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_group = first_object.group

        self.assertEqual(post_text, text)
        self.assertEqual(post_group, group)

    def test_post_not_in_another_group(self):
        """Проверка: пост не попал в другую группу."""
        text = self.post.text
        view = self.views_dict['group_posts']
        response = self.authorized_client.get(view)

        first_object = response.context['page_obj'][0]
        post_text = first_object.text

        self.assertIn(post_text, text)
        self.assertNotEqual(self.group.slug, 'test_group_slug_other')

    def test_post_not_in_another_group(self):
        """Проверка: пост не попал в другой профиль."""
        text = self.post.text
        author = self.post_author.username
        view = self.views_dict['group_posts']

        response = self.authorized_client.get(view)
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author = first_object.author

        self.assertIn(post_text, text)
        self.assertNotEqual(post_author, author)

    def test_first_page_ten_posts(self):
        """Проверка: количество постов на первой странице равно 10."""
        namespace_list = {
            'posts:index': reverse('posts:index'),
            'posts:group_posts': reverse('posts:group_posts',
                                         kwargs={'slug': self.group.slug}),
            'posts:profile': reverse('posts:profile',
                                     kwargs={'username':
                                             self.post_author.username}),
        }

        for template, reverse_name in namespace_list.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']
                                 ), settings.POSTS_PER_PAGE)

    def test_third_page_contains_six_posts(self):
        """Проверка: количество постов на 3 странице равно 6
        count количество постов созданых в цикле
         + 1 пост в не цикла count+1//10 = 6."""
        namespace_list = {
            'posts:index': reverse('posts:index') + '?page=3',
            'posts:group_posts': reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}) + '?page=3',
            'posts:profile': reverse(
                'posts:profile',
                kwargs={'username': self.post_author.username}) + '?page=3',
        }
        count_posts = (self.count_post + 1) % settings.POSTS_PER_PAGE
        for template, reverse_name in namespace_list.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']), count_posts)
