from django.shortcuts import render, redirect
from django.contrib import messages
from . import forms

def Training_Request_New(request):
    if request.method == 'POST':
        form = forms.RequestTraining(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your training request has been submitted.')
            return redirect('training:training_request')
    else:
        form = forms.RequestTraining()

    return render(request, 'training/training_request.html', {'form': form})



