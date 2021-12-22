from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import get_paginator


def index(request):
    context = {
        'index': True,
    }
    context.update(get_paginator(
        Post.objects.select_related('group').all(),
        request)
    )
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    context = {
        'group': group,
    }
    context.update(get_paginator(
        Post.objects.filter(group=group),
        request)
    )
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    num_post = Post.objects.filter(author__username=username).count()
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    context = {
        'author': author,
        'following': following,
        'num_post': num_post,
    }
    context.update(get_paginator(
        Post.objects.filter(author__username=username),
        request)
    )
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comment = Comment.objects.filter(post_id=post.id)
    num_post = Post.objects.filter(author__username=post.author).count()
    context = {
        'post': post,
        'num_post': num_post,
        'comments': comment,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=post.author.username)


@login_required
def post_edit(request, post_id,):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        return render(
            request, 'posts/create_post.html',
            {'form': form, 'is_edit': True, 'post': post}
        )
    form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    context = {
        'follow': True,
    }
    context.update(get_paginator(
        Post.objects.filter(author__following__user=request.user),
        request)
    )
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=username)
    if request.user != user:
        Follow.objects.get_or_create(
            user_id=request.user.id,
            author_id=user.id
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=username)
    Follow.objects.filter(user_id=request.user.id, author_id=user.id).delete()
    return redirect('posts:profile', username=username)
