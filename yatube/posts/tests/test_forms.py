from tokenize import group
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post
from posts.forms import PostForm
import posts.views


User = get_user_model()


class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """ Создаем тестовую группу и тестовый экземпляр поста."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_test')
        cls.user2= User.objects.create_user(username='test_test2')
        cls.group = Group.objects.create(
            title='Тестовая заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date='Тестовая дата',
            author=cls.user2,
            group=cls.group,
        )
        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author.force_login(self.user2)

    def test_authorized_client_post_create(self):
        """Авторизированный клиент может создавать посты."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.pk,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}))
        self.assertTrue(
            Post.objects.filter(text='Данные из формы', author=self.user, group = self.group).exists()
        )

    def test_guest_client_can_not_post_create(self):
        """Неавторизованный клиент не может создавать посты."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Пост от неавторизованного клиента',
            'group': self.group.id
        }

        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )

        self.assertFalse(Post.objects.filter(
            text='Пост от неавторизованного клиента').exists())
        self.assertEqual(Post.objects.count(), posts_count)

    def test_author_post_edit(self):
        """Автор может редактировать посты не автор будет перенаправлен."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Измененный текст',
            'group': self.group.id
        }

        response = self.author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            #ollow=True
        )

        self.assertEqual(Post.objects.count(), post_count)
        # self.assertRedirects(response, reverse(
        #     'posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertTrue(
            Post.objects.filter(text='Измененный текст', author = self.user2, group = self.group).exists()
        )

    def test_authorized_post_edit(self):
        """ не автор будет перенаправлен."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Измененный текст2',
            'group': self.group.id
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            #follow=True
        )

        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertFalse(
            Post.objects.filter(text='Измененный текст2', author = self.user2, group = self.group).exists()
        )
