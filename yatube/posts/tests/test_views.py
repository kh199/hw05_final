import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
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
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': self.group.slug})
            ),
            'posts/profile.html': (
                reverse('posts:profile',
                        kwargs={'username': self.user.username})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': self.post.id})
            ),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_pages_uses_correct_template(self):
        """URL-адрес post_edit использует шаблон posts/create_post.html."""
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                        kwargs={'post_id': self.post.id})))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_post_show_picture(self):
        """Проверка картинки."""
        templates_pages_names = {
            reverse('posts:index'): self.post.image,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): self.post.image,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): self.post.image,
        }
        for value, expected in templates_pages_names.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.image, expected)

    def test_post_show_picture(self):
        """Проверка картинки на странице поста."""
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                        kwargs={'post_id': self.post.id})))
        post = response.context['post']
        self.assertEqual(post.image, self.post.image)

    def test_post_show_correct_text(self):
        """Проверка текста первого поста."""
        templates_pages_names = {
            reverse('posts:index'): self.post.text,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): self.post.text,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): self.post.text,
        }
        for value, expected in templates_pages_names.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.text, expected)

    def test_post_show_correct_post_id(self):
        """Проверка id первого поста."""
        templates_pages_names = {
            reverse('posts:index'): self.post.id,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): self.post.id,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): self.post.id,
        }
        for value, expected in templates_pages_names.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.id, expected)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list передает список постов группы."""
        response = (self.authorized_client.
                    get(reverse('posts:group_list',
                        kwargs={'slug': self.group.slug})))
        group = response.context['group']
        self.assertEqual(group, Group.objects.get(slug=self.group.slug))

    def test_profile_page_show_correct_context(self):
        """Шаблон profile передает список постов пользователя."""
        response = (self.authorized_client.
                    get(reverse('posts:profile',
                        kwargs={'username': self.user.username})))
        author = response.context['author']
        num_post = response.context['num_post']
        self.assertEqual(author, User.objects.get(username=self.user.username))
        self.assertEqual(num_post, Post.objects.filter(
            author__username=self.user.username
        ).count())

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail передает один пост, отфильтрованный по id."""
        response = (self.authorized_client.
                    get(reverse('posts:post_detail',
                        kwargs={'post_id': self.post.id})))
        post = response.context['post']
        num_post = response.context['num_post']
        self.assertEqual(post, Post.objects.get(id=self.post.id))
        self.assertEqual(num_post, 1)

    def test_create_post_show_correct_context(self):
        """Шаблон create_post передает форму создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_pages_show_correct_context(self):
        """Шаблон create_post передает форму редактирования поста."""
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                        kwargs={'post_id': self.post.id})))
        post = response.context['post']
        self.assertEqual(post, Post.objects.get(id=self.post.id))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.user = User.objects.create_user(username='TestUser2')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        self.post = Post.objects.bulk_create(
            [
                Post(
                    text='Тестируем  паджинатор',
                    author=self.user,
                    group=self.group,
                ),
            ] * 13
        )

    def test_first_page_contains_ten_records(self):
        templates_pages_names = {
            reverse('posts:index'): settings.POSTS_PER_PAGE,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): settings.POSTS_PER_PAGE,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}):
            settings.POSTS_PER_PAGE,
        }
        for reverse_template, expected in templates_pages_names.items():
            with self.subTest(reverse_template=reverse_template):
                response = self.client.get(reverse_template)
                self.assertEqual(len(response.context['page_obj']), expected)

    def test_second_page_contains_three_records(self):
        all_posts = Post.objects.filter(
            author__username=self.user.username
        ).count()
        second_page_posts = all_posts - settings.POSTS_PER_PAGE
        templates_pages_names = {
            reverse('posts:index'): second_page_posts,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): second_page_posts,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}):
            second_page_posts,
        }
        for reverse_template, expected in templates_pages_names.items():
            with self.subTest(reverse_template=reverse_template):
                response = self.client.get(reverse_template + '?page=2')
                self.assertEqual(len(response.context['page_obj']), expected)
