from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from taggit.models import Tag

from .models import Post


def posts_list(request, tag_slug=None):
    posts = Post.objects.all().order_by('-date')
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts = posts.filter(tags__in=[tag])

    paginator = Paginator(posts, 3)
    posts = paginator.get_page(request.GET.get('page'))

    return render(request, 'posts/posts_list.html', {'posts': posts, 'tag': tag})


def post_page(request, slug):
    post = get_object_or_404(Post, slug=slug)
    return render(request, 'posts/post_page.html', {'post': post})
