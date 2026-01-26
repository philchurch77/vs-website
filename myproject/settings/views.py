from django.shortcuts import render

def homepage(request):
    return render(request, 'home.html')

def posts_list(request):
    return render(request, 'posts/posts_list.html')

