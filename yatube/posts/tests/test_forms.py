import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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
            group=self.group
        )

    def test_create_post_with_picture(self):
        """Валидная форма с картинкой создает запись."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст с картинкой',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_object = response.context['page_obj'][0]
        self.assertEqual(last_object.text, form_data['text'])
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                image=last_object.image
            ).exists()
        )

    def test_create_post_without_group(self):
        """Создание поста без группы"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Пост без группы',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_object = response.context['page_obj'][0]
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(last_object.text, form_data['text'])

    def test_create_group_post(self):
        """Создание поста группы"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Пост группы',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_object = response.context['page_obj'][0]
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(last_object.text, form_data['text'])
        self.assertEqual(last_object.group.id, form_data['group'])

    def test_edit_post_without_group(self):
        """Редактирование поста без группы"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста без группы',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        post_context = response.context['post']
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post_context.text, form_data['text'])

    def test_edit_group_post(self):
        """Редактирование поста с группой"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста с группой',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        post_context = response.context['post']
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post_context.text, form_data['text'])
        self.assertEqual(post_context.group.id, form_data['group'])

    def test_create_post_by_guest(self):
        """Создание поста неавторизированным пользователем"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Пытаемся создать пост',
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        create_url = reverse('posts:post_create')
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next={create_url}')
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post_by_guest(self):
        """Редактирование поста неавторизированным пользователем"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный пост',
        }
        response = self.client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        edit_url = reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next={edit_url}')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(self.post.text, self.post.text)
        self.assertNotEqual(self.post.text, form_data['text'])

    def test_add_comments_by_guest(self):
        """Добавление комментария неавторизированным пользователем"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Комментарий от гостя',
        }
        response = self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_add_comments_by_authorized_user(self):
        """Добавление комментария авторизированным пользователем"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Пишем комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        last_comment = response.context['comments'][0]
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(last_comment.text, form_data['text'])
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                post_id=self.post.id
            ).exists()
        )
