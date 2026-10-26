from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from django import get_version


def home(request):
    context = {
        "django_version": get_version(),
        "server_time": timezone.localtime(timezone.now()),
        "debug": settings.DEBUG,
    }
    return render(request, "config/home.html", context)
