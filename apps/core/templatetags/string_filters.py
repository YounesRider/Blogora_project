from django import template

register = template.Library()

@register.filter
def first_char(value):
    """Return the first character of a string."""
    if value:
        return str(value)[0]
    return ''
