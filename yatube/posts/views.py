from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

from .forms import PostForm
from .models import Group, Post
from .utils import post_paginator


User = get_user_model()


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form = form.save(commit=False)
            form.author = request.user
            form.save()
            return redirect('posts:profile', username=form.author.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post.id)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post.id)
    else:
        form = PostForm(instance=post)
    context = {'form': form, 'post_id': post_id}
    return render(request, 'posts/create_post.html',
                  context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    count_post = Post.objects.filter(author=post.author_id).count()
    context = {
        'post': post,
        'count_post': count_post,
    }
    return render(request, 'posts/post_detail.html', context)


def index(request):
    page_obj = post_paginator(Post.objects.all(), request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = post_paginator(group.posts.all(), request)
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    count_post = author.posts.all().count()
    page_obj = post_paginator(author.posts.all(), request)
    context = {
        'author': author,
        'count_post': count_post,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)
