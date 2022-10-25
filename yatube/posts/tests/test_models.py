from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Post
from posts.models import Group


User = get_user_model()


class TaskModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """ Создаем тестового пользвателья и тестовый экземпляр поста."""
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='test_test',
                                            email='test@test.com',
                                            password='qwerty1234',),
            text='Test text test text'
        )

        cls.group = Group.objects.create(
            title='test_group title',
            slug='test_group_slug',
            description='test_group description',
            )

    def test_object_post_text(self):
        """Тест--первые пятнадцать символов поста"""
        post = TaskModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_object_group_is_title_fild(self):
        """Тест--название группы"""
        group = TaskModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
