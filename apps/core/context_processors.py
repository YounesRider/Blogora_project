from django.conf import settings


def site_name(request):
    """
    Add SITE_NAME to all templates.
    """
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'Blogora'),
    }
