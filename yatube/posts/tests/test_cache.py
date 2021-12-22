from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group,
        )

    def test_cache_index_page(self):
        """Проверка кеширования главной страницы"""
        response = self.client.get(reverse('posts:index'))
        Post.objects.filter(id=self.post.id).exists()
        Post.objects.get(id=self.post.id).delete()
        self.assertTrue(self.post.text.encode() in response.content)
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertFalse(self.post.text.encode() in response.content)
