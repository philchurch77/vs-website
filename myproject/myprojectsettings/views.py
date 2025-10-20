from django.shortcuts import render

def homepage(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def posts_list(request):
    return render(request, 'posts/posts_list.html')

