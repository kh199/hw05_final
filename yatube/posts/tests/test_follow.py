from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Post

User = get_user_model()


class FollowViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestAuthor')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост автора',
        )

    def setUp(self):
        self.user = User.objects.create_user(username='TestFollower')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_autorized_user_can_follow(self):
        """Пользователь может подписываться на авторов"""
        follow_count = Follow.objects.count()
        author = FollowViewsTests.user
        response = (self.authorized_client.
                    get(reverse('posts:profile_follow',
                        kwargs={'username': author.username})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=author
        ).exists)

    def test_autorized_user_can_unfollow(self):
        """Пользователь может отписываться от авторов"""
        author = FollowViewsTests.user
        self.authorized_client.get(reverse('posts:profile_follow',
                                   kwargs={'username': author.username}))
        follow_count = Follow.objects.count()
        response = (self.authorized_client.
                    get(reverse('posts:profile_unfollow',
                        kwargs={'username': author.username})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=author
        ).exists())

    def test_autorized_user_can_follow_once(self):
        """Можно подписаться на автора только один раз"""
        follow_count = Follow.objects.count()
        author = FollowViewsTests.user
        response = (self.authorized_client.
                    get(reverse('posts:profile_follow',
                        kwargs={'username': author.username})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=author
        ).exists)
        follow_count = Follow.objects.count()
        response = (self.authorized_client.
                    get(reverse('posts:profile_follow',
                        kwargs={'username': author.username})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=author
        ).exists)

    def test_autorized_user_cant_follow_yourself(self):
        """Нельзя подписаться на самого себя"""
        follow_count = Follow.objects.count()
        response = (self.authorized_client.
                    get(reverse('posts:profile_follow',
                        kwargs={'username': self.user.username})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=self.user
        ).exists())

    def test_follow_index(self):
        """Проверка работы ленты Избранные авторы"""
        author = FollowViewsTests.user
        self.authorized_client.get(reverse('posts:profile_follow',
                                   kwargs={'username': author.username}))
        response = (self.authorized_client.get(reverse('posts:follow_index')))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.id, self.post.id)
        self.authorized_client.get(reverse('posts:profile_unfollow',
                                   kwargs={'username': author.username}))
        response = (self.authorized_client.get(reverse('posts:follow_index')))
        self.assertNotContains(response, self.post.text)
