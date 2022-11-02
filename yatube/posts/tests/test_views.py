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
        self.index_v = 'posts:index'
        self.profile_v = 'posts:profile'
        self.post_detail_v = 'posts:post_detail'
        self.create_v = 'posts:post_create'
        self.edit_v = 'posts:post_edit'
        self.group_posts_v = 'posts:group_posts'
        self.templates_page_names = {
            reverse(self.group_posts_v, kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            reverse(self.index_v): 'posts/index.html',
            reverse(self.profile_v, kwargs={'username': (
                self.post_author.username)}): 'posts/profile.html',
            reverse(self.create_v): 'posts/create_post.html',
            reverse(self.edit_v, kwargs={'post_id': (
                self.post.pk)}): 'posts/create_post.html',
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
        rev = reverse(self.index_v)

        response = self.guest_client.get(rev)
        first_object = response.context['page_obj'][0]
        text = first_object.text
        author = first_object.author

        self.assertEqual(text, post_text)
        self.assertEqual(author, post_author)
        self.assertEqual(len(response.context['page_obj']), len(page_obj))

    def test_posts_group_posts_get_correct_context(self):
        """Шаблон group_posts сформированы с верным контекстом."""
        post_group = self.group
        page_obj = page_obj_func(post_group.posts.all(), 1)

        rev = reverse(self.group_posts_v, kwargs={'slug': self.group.slug})
        response = self.guest_client.get(rev)
        group = response.context['group']

        self.assertEqual(group, post_group)
        self.assertEqual(len(response.context['page_obj']), len(page_obj))

    def test_posts_profile_get_correct_context(self):
        """Шаблон profile сформированы с верным контекстом."""
        author = self.post_author
        count = self.count_post + 1
        page_obj = page_obj_func(author.posts.all(), 1)
        rev = reverse(self.profile_v, kwargs={'username': (
                      self.post_author.username)})

        response = self.guest_client.get(rev)
        count_posts = response.context['count_post']
        post_author = response.context['author']

        self.assertEqual(count_posts, count)
        self.assertEqual(post_author, author)
        self.assertEqual(len(response.context['page_obj']), len(page_obj))

    def test_posts_post_detail_get_correct_context(self):
        """Шаблон post_detail сформированы с верным контекстом."""
        post = self.post
        author = self.post_author
        count = self.count_post + 1
        rev = reverse(self.post_detail_v, args=[self.post.id])

        response = self.guest_client.get(rev)
        first_object = response.context['post']
        count_posts = response.context['count_post']
        post_author = first_object.author

        self.assertEqual(first_object, post)
        self.assertEqual(count_posts, count)
        self.assertEqual(post_author, author)

    def test_create_post_show_correct_context_create(self):
        """Шаблон create с верным контекстом."""
        view = reverse(self.create_v)

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
        rev = reverse(self.edit_v, kwargs={'post_id': (self.post.pk)})
        postid = self.post.id

        response = self.authorized_client.get(rev)
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
        """Проверка: пост попал в нужную группу."""
        group = self.group
        post = self.post
        rev = reverse(self.group_posts_v, kwargs={'slug': self.group.slug})

        response = self.authorized_client.get(rev)
        post_group = response.context['group']

        self.assertIn(post, response.context['page_obj'])
        self.assertEqual(post_group, group)

    def test_post_not_in_another_group(self):
        """Проверка: пост не попал в другую группу."""
        post = self.post
        v = reverse(self.group_posts_v, kwargs={'slug': self.group_other.slug})
        response = self.authorized_client.get(v)
        self.assertNotContains(response, post)

    def test_post_not_in_another_profile(self):
        """Проверка: пост не попал в другой профиль."""
        post = self.post
        rev = reverse(self.profile_v,
                      kwargs={'username': (self.not_author.username)})

        response = self.authorized_client.get(rev)

        self.assertNotContains(response, post)

    def test_post_not_in_another_profile(self):
        """Проверка: пост попал в нужный профиль."""
        post = self.post
        rev = reverse(self.profile_v,
                      kwargs={'username': (self.post_author.username)})

        response = self.authorized_client.get(rev)

        self.assertContains(response, post)

    def test_first_page_ten_posts(self):
        """Проверка: количество постов на первой странице равно 10."""
        namespace_list = [
            reverse(self.index_v),
            reverse(self.group_posts_v, kwargs={'slug': self.group.slug}),
            reverse(self.profile_v,
                    kwargs={'username': (self.post_author.username)})
        ]

        for reverse_name in namespace_list:
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
