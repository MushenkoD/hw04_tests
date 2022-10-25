from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post


User = get_user_model()


class PostURLTest(TestCase):

    @classmethod
    def setUpClass(cls):
        """ Создаем тестовую группу и тестовый экземпляр поста."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_test')
        cls.group = Group.objects.create(
            title = 'test_group title',
            slug = 'test_group_slug',
            description = 'test_group description',
        )
        
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test text test text',
        )

    def setUp(self):
        """Создаем неавторизованный клиент, cоздаем авторизованный клиент
        и авторизованный клиент автора поста
        и авторизуем пользователей"""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user)

  
    def test_list_url_exists_at_desired_location(self):
        """Страница /--(главная) доступна любому пользователю."""
        urls = (reverse('posts:index'),
                reverse('posts:group_posts',
                        kwargs={'slug': self.group.slug}),
                reverse('posts:profile',
                        kwargs={'username': self.user.username}),
                reverse('posts:post_detail', args=[self.post.id]),
                )
        for url in urls:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)
        response = self.guest_client.get('/qwerty12345/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)

    def test_url_post_create(self):
        """Страница /create/--(создания поста) доступна 
        только авторизованному пользователю."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_url_post_edit(self):
        """Страница /posts/post_id/edit --(редактирования поста) 
        доступна только автору поста."""
        if self.user.username == self.post.author:
            response = self.authorized_client. \
                get(reverse('posts:post_edit',
                            kwargs={'post_id': f'{self.post.id}'}))
            self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_task_list_url_redirect_anonymous_on_admin_login(self):
        """Адрес /create/ --(создания поста)
         перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get(reverse('posts:post_create'),
                                         follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_to_login(self):
        """Адрес /posts/post_id/edit --(редактирования поста)
        перенаправит анонимного пользователя
        на страницу авторизации.
        """
        response = self.client. \
            get(reverse('posts:post_edit',
                        kwargs={'post_id': f'{self.post.id}'}), follow=True)
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.id}/edit/')

    def test_urls_uses_correct_template(self):
        """Проверка соответствия URL-адреса и шаблона."""
        templates_url_names = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail', args=[self.post.id]):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

