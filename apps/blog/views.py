from django.http import HttpResponse


def home(request):
    return HttpResponse("<h1>Welcome to Smart Blog AI</h1><p>Your Django site is running.</p>")
