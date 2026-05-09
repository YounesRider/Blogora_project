from django import template

register = template.Library()

@register.filter
def status_color(status):
    """Return Bootstrap color class for article status."""
    colors = {
        'draft': 'secondary',
        'pending_review': 'warning',
        'published': 'success',
        'rejected': 'danger',
        'archived': 'dark'
    }
    return colors.get(status, 'secondary')

@register.filter
def role_color(role):
    """Return Bootstrap color class for user role."""
    colors = {
        'guest': 'light',
        'user': 'primary',
        'author': 'info',
        'admin': 'danger'
    }
    return colors.get(role, 'secondary')
