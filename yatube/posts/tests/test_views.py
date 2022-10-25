from django import forms
from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model


from posts.models import Post, Group


User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """ Создаем тестовую группу и тестовыый экземпляр поста 
        и 25 тестовых постов для теста пагинатора."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_test')
        cls.group = Group.objects.create(
            title = 'test_group title',
            slug = 'test_group_slug',
            description = 'test_group description',
        )
        cls.post = Post.objects.create(
            text='Test text test text',
            author=cls.user,
            group=cls.group,
        )
        count = 25
        for post_number in range(count):
            cls.post = Post.objects.create(
                text='Test text test text',
                author=cls.user,
                group=cls.group,
        )

    def setUp(self):
        """Создаем неавторизованный клиент, cоздаем авторизованный клиент
        и авторизуем пользователя"""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)


    
    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон"""
        templates_page_names = {
            'posts/group_list.html' :reverse('posts:group_posts', kwargs={'slug': self.group.slug}) ,
            'posts/index.html': reverse('posts:index') ,
            'posts/profile.html': reverse('posts:profile', kwargs={'username': (
                self.user.username)}), 
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/create_post.html' :reverse('posts:post_edit', kwargs={'post_id': (
                self.post.pk)}),
        }
        for template , reverse_name  in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
    

    def test_posts_get_correct_context(self):
        """Шаблоны posts сформированы с верным контекстом."""
        namespace_list = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_posts', args=[self.group.slug]): 'page_obj',
            reverse('posts:profile', args=[self.user.username]): 'page_obj',
            reverse('posts:post_detail', args=[self.post.pk]): 'post',
        }
        for reverse_name, context in namespace_list.items():
            first_object = self.guest_client.get(reverse_name)
            if context == 'post':
                first_object = first_object.context[context]
            else:
                first_object = first_object.context[context][0]
            post_text = first_object.text
            post_author = first_object.author
            post_group = first_object.group
            posts_dict = {
                post_text: self.post.text,
                post_author: self.user,
                post_group: self.group,
            }
            for post_param, test_post_param in posts_dict.items():
                with self.subTest(
                        post_param=post_param,
                        test_post_param=test_post_param):
                    self.assertEqual(post_param, test_post_param)


    def test_create_post_show_correct_context(self):
        """Шаблоны create и edit сформированы с верным контекстом."""
        namespace_list = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=[self.post.pk])
        ]
        for reverse_name in namespace_list:
            response = self.authorized_client.get(reverse_name)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_post_in_another_group(self):
        """Проверка: пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_posts', args={self.group.slug}))
        first_object = response.context["page_obj"][0]
        post_text = first_object.text
        self.assertTrue(post_text, 'Test text test text')


    def test_first_page_ten_posts(self):
        """Проверка: количество постов на первой странице равно 10."""
        namespace_list = {
            'posts:index': reverse('posts:index'),
            'posts:group_posts': reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug}),
            'posts:profile': reverse(
            'posts:profile', kwargs={'username': self.user.username}),
        }
        count_posts = 10
        for template, reverse_name in namespace_list.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']), count_posts)

    def test_third_page_contains_six_posts(self):
        """Проверка: количество постов на 3 странице равно 6. 
        count количество постов созданых в цикле
         + 1 пост в не цикла count+1//10 = 6"""
        namespace_list = {
            'posts:index': reverse('posts:index') + "?page=3",
            'posts:group_posts': reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}) + "?page=3",
            'posts:profile': reverse(
                'posts:profile',
                kwargs={'username': self.user.username}) + "?page=3",
        }
        count_posts = 6
        for template, reverse_name in namespace_list.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']), count_posts)

