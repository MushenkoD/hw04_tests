from http import HTTPStatus

from django import forms
from django.urls import reverse
from django.test import TestCase, Client
from django.conf import settings
from django.contrib.auth import get_user_model

from posts.models import Post, Group


User = get_user_model()

POSTS_PER_PAGE = settings.POSTS_PER_PAGE

count_post = POSTS_PER_PAGE * 2 + 5


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """ Создаем тестовую группу и тестовыый экземпляр поста
        и 25 тестовых постов для теста пагинатора."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_test')
        cls.user2 = User.objects.create_user(username='test_test2')
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
            author=cls.user,
            group=cls.group,
        )

        for post_number in range(count_post):
            cls.post = Post.objects.create(
                text='Test text test text',
                author=cls.user,
                group=cls.group,
            )

    def setUp(self):
        """Создаем неавторизованный клиент, cоздаем авторизованный клиент
        и авторизуем пользователя и словарь шаблонов."""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.templates_page_names = {
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile', kwargs={'username': (
                self.user.username)}): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': (
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
        author = self.user
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author = first_object.author
        self.assertEqual(post_text, 'Test text test text')
        self.assertEqual(post_author, author)

    def test_posts_group_posts_get_correct_context(self):
        """Шаблон group_posts сформированы с верным контекстом."""
        group = self.group
        response = self.guest_client.get(
            reverse('posts:group_posts', args=[self.group.slug]))
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_group = first_object.group
        self.assertEqual(post_text, 'Test text test text')
        self.assertEqual(post_group, group)

    def test_posts_profile_get_correct_context(self):
        """Шаблон profile сформированы с верным контекстом."""
        post = self.post
        count = count_post + 1
        response = self.guest_client.get(
            reverse('posts:profile', args=[self.user.username]))
        first_object = response.context['page_obj'][0]
        count_posts = Post.objects.filter(author=post.author_id).count()
        post_text = first_object.text
        self.assertEqual(post_text, 'Test text test text')
        self.assertEqual(count_posts, count)

    def test_posts_post_detail_get_correct_context(self):
        """Шаблон post_detail сформированы с верным контекстом."""
        author = self.user
        count = count_post + 1
        response = self.guest_client.get(
            reverse('posts:post_detail', args=[self.post.id]))
        first_object = response.context['post']
        count_posts = author.posts.all().count()
        post_text = first_object.text
        post_author = first_object.author
        self.assertEqual(post_text, 'Test text test text')
        self.assertEqual(count_posts, count)
        self.assertEqual(post_author, author)

    def test_create_post_show_correct_context_create(self):
        """Шаблон create с верным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_correct_context_edit(self):
        """Шаблон edit с верным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=[self.post.pk]))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_in_this_group(self):
        """Проверка: пост  группу."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', args={self.group.slug}))
        first_object = response.context["page_obj"][0]
        post_text = first_object.text
        self.assertIn(post_text, 'Test text test text')
        self.assertEqual(self.group.slug, 'test_group_slug')

    def test_post_not_in_another_group(self):
        """Проверка: пост не попал в другую группу."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', args={self.group.slug}))
        first_object = response.context["page_obj"][0]
        post_text = first_object.text
        self.assertIn(post_text, 'Test text test text')
        self.assertNotEqual(self.group.slug, 'test_group_slug_other')

    def test_post_not_in_another_group(self):
        """Проверка: пост не попал в другой профиль."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': (self.user.username)}))
        first_object = response.context["page_obj"][0]
        post_text = first_object.text
        self.assertIn(post_text, 'Test text test text')
        self.assertNotEqual(self.user.username, 'test_test2')

    def test_first_page_ten_posts(self):
        """Проверка: количество постов на первой странице равно 10."""
        namespace_list = {
            'posts:index': reverse('posts:index'),
            'posts:group_posts': reverse(
                'posts:group_posts', kwargs={'slug': self.group.slug}),
            'posts:profile': reverse(
                'posts:profile', kwargs={'username': self.user.username}),
        }
        for template, reverse_name in namespace_list.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']), POSTS_PER_PAGE)

    def test_third_page_contains_six_posts(self):
        """Проверка: количество постов на 3 странице равно 6
        count количество постов созданых в цикле
         + 1 пост в не цикла count+1//10 = 6."""
        namespace_list = {
            'posts:index': reverse('posts:index') + "?page=3",
            'posts:group_posts': reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}) + "?page=3",
            'posts:profile': reverse(
                'posts:profile',
                kwargs={'username': self.user.username}) + "?page=3",
        }
        count_posts = (count_post + 1) % POSTS_PER_PAGE
        for template, reverse_name in namespace_list.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']), count_posts)
