from django.shortcuts import render, redirect, get_object_or_404
from .models import Topic
from taggit.models import Tag
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def resource_list(request):
    qs = Topic.objects.select_related('author').prefetch_related('tags').order_by('-date')
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, "resources/resources_list.html", {"resources": page_obj})

def resource_list_by_tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    qs = Topic.objects.filter(tags__in=[tag]).select_related('author').prefetch_related('tags').order_by('-date')
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, "resources/resources_list.html", {"resources": page_obj})

def resource_page(request, slug):
    topic = get_object_or_404(Topic.objects.select_related('author').prefetch_related('tags'), slug=slug)
    return render(request, 'resources/resources_page.html', {'topic': topic})