from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseNotFound, HttpResponseServerError

def home(request):
    """
    Renders the home page.
    """
    # This view likely needs context data for the homepage.
    # For now, it just renders the template.
    return render(request, 'home.html')

def about(request):
    """
    Renders the about page.
    """
    return render(request, 'static_pages/about.html')

def contact(request):
    """
    Renders the contact page.
    """
    return render(request, 'static_pages/contact.html')

def teachers(request):
    """
    Renders the teachers list page.
    """
    return render(request, 'static_pages/teachers.html')

def faq(request):
    """
    Renders the FAQ page.
    """
    return render(request, 'faq.html')


def handler404(request, exception, template_name='404.html'):
    """
    Custom 404 error handler.
    """
    context = {
        'title': 'Page Not Found',
        'message': 'The page you are looking for does not exist.'
    }
    return HttpResponseNotFound(render(request, 'errors/404.html', context))


def handler500(request, template_name='500.html'):
    """
    Custom 500 error handler.
    """
    context = {
        'title': 'Server Error',
        'message': 'An error occurred while processing your request.'
    }
    return HttpResponseServerError(render(request, 'errors/500.html', context))


def privacy(request):
    """
    Renders the privacy policy page.
    """
    return render(request, 'privacy.html')


def terms(request):
    """
    Renders the terms of service page.
    """
    return render(request, 'terms.html')