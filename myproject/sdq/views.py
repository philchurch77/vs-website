from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .forms import SDQForm
from .models import SDQResponse

@login_required
def sdq_view(request):
    form = SDQForm(request.POST or None)
    response = None
    if request.method == "POST" and form.is_valid():
        # Build a model instance from the form data (not saved).
        # sdq_form.html promises results are never stored — do not add
        # .save() without updating that copy and running a DPIA check.
        response = SDQResponse(**form.cleaned_data)

    return render(request, "sdq/sdq_form.html", {"form": form, "response": response})