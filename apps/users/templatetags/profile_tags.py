from django import template

register = template.Library()

@register.filter
def checked_if_selected(is_selected):
    """Retourne 'checked' si l'élément est sélectionné."""
    return 'checked' if is_selected else ''
