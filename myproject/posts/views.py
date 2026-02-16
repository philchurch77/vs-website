from django.shortcuts import render, redirect, get_object_or_404
from .models import Post
from taggit.models import Tag
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from . import forms

def posts_list(request, tag_slug=None):
    posts = Post.objects.all().order_by('-date')
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts = posts.filter(tags__in=[tag])

    paginator = Paginator(posts, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(request, 'posts/posts_list.html', {'posts': posts, 'tag': tag})

def post_page(request, slug):
    post = get_object_or_404(Post, slug=slug)
    return render(request, 'posts/post_page.html', {'post': post})

# Post creation via website form is disabled. Please use the admin interface to create posts.

