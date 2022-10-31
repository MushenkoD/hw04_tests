from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Group, Post


User = get_user_model()


class PostURLTest(TestCase):

    @classmethod
    def setUpClass(cls):
        """ Создаем тестовую группу и тестовый экземпляр поста."""
        super().setUpClass()
        cls.not_author = User.objects.create_user(username='test_test1')
        cls.post_author = User.objects.create_user(username='test_test2')
        cls.group = Group.objects.create(
            title='test_group title',
            slug='test_group_slug',
            description='test_group description',
        )

        cls.post = Post.objects.create(
            author=cls.post_author,
            text='Test text test text',
        )
        cls.index_url =    '/'
        cls.group_list_url =    f'/group/{cls.group.slug}/'
        cls.profile_url =   f'/profile/{cls.not_author.username}/'
        cls.post_detail_url =    f'/posts/{cls.post.id}/'
        cls.create_post_url =   '/create/'
        cls.edit_url =    f'/posts/{cls.post.id}/edit/'

        cls.index_url_t =    'posts/index.html'
        cls.group_list_t =   'posts/group_list.html'
        cls.profile_t =    'posts/profile.html'
        cls.post_detail_t =    'posts/post_detail.html'
        cls.create_post_t  =   'posts/create_post.html'
        cls.edit_t =    'posts/create_post.html'
    def setUp(self):
        """Создаем неавторизованный клиент, cоздаем авторизованный клиент
        и авторизованный клиент автора поста
        и авторизуем пользователей."""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.not_author)
        self.author_client = Client()
        self.author_client.force_login(self.post_author)
        # self.templates_url_names = {
        #     '/': 'posts/index.html',
        #     f'/group/{self.group.slug}/': 'posts/group_list.html',
        #     f'/profile/{self.not_author.username}/': 'posts/profile.html',
        #     f'/posts/{self.post.id}/': 'posts/post_detail.html',
        #     '/create/': 'posts/create_post.html',
        #     f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
        # }
        # self.urls = {
        #     'index': '/',
        #     'group_list': f'/group/{self.group.slug}/',
        #     'profile': f'/profile/{self.not_author.username}/',
        #     'post_detail': f'/posts/{self.post.id}/',
        #     'create': '/create/',
        #     'edit': f'/posts/{self.post.id}/edit/',
        # }
        # self.open_urls = {k: self.urls[k] for k in list(self.urls.keys())[:4]}

    def test_url_not_exist(self):
        """Страница не существующая не существует."""
        response = self.guest_client.get('/unexistsng_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_list_url_exists_at_desired_location(self):
        """Страницы доступные любому пользователю."""
        open_urls = {
            self.index_url : self.index_url_t,
            self.group_list_url : self.group_list_t,
            self.profile_url : self.profile_t,
            self.post_detail_url : self.post_detail_t,
        }

        for address, template in open_urls.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_post_create(self):
        """Страница /create/--(создания поста) доступна
        только авторизованному пользователю."""
        response = self.authorized_client.get(self.create_post_url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_post_create_not_avaible_guest(self):
        """Страница /create/--(создания поста) не доступна
        не авторизованному пользователю."""
        response = self.guest_client.get(self.create_post_url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_url_post_edit(self):
        """Страница /posts/post_id/edit --(редактирования поста)
        доступна автору поста."""
        self.post_author.username = self.post.author

        response = self.author_client.get(self.edit_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_post_edit1(self):
        """Страница /posts/post_id/edit --(редактирования поста)
        не доступна не автору поста."""
        self.post_author.username = self.post.author

        response = self.authorized_client.get(self.edit_url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, self.post_detail_url)
        #self.assertTemplateUsed(response, self.post_detail_t)

    def test_post_edit_to_login(self):
        """Адрес /posts/post_id/edit --(редактирования поста)
        перенаправит анонимного пользователя
        на страницу авторизации."""
        response = self.client.get(self.edit_url)

        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.id}/edit/')

    def test_urls_uses_correct_template(self):
        """Проверка соответствия URL-адреса и шаблона."""
        templates_url_names = {
            self.index_url : self.index_url_t,
            self.group_list_url : self.group_list_t,
            self.profile_url : self.profile_t,
            self.post_detail_url : self.post_detail_t,
            self.create_post_url : self.create_post_t,
            self.edit_url : self.edit_t,
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)
