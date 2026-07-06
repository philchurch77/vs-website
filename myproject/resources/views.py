from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Topic
from taggit.models import Tag
from django.core.paginator import Paginator

@login_required
def resource_list(request):
    qs = Topic.objects.select_related('author').prefetch_related('tags').order_by('-date')
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, "resources/resources_list.html", {"resources": page_obj, "tag": None})

@login_required
def resource_list_by_tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    qs = Topic.objects.filter(tags__in=[tag]).select_related('author').prefetch_related('tags').order_by('-date')
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, "resources/resources_list.html", {"resources": page_obj, "tag": tag})

@login_required
def resource_page(request, slug):
    topic = get_object_or_404(Topic.objects.select_related('author').prefetch_related('tags'), slug=slug)
    return render(request, 'resources/resources_page.html', {'topic': topic})