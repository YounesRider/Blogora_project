from django import template

register = template.Library()


@register.filter
def first_char(value):
    """Returns the first character of a string."""
    if not value:
        return ''
    return str(value)[0]


@register.filter
def status_color(status):
    """Returns Bootstrap color class based on article status."""
    status_colors = {
        'draft': 'secondary',
        'pending_review': 'warning', 
        'published': 'success',
        'rejected': 'danger',
        'archived': 'dark'
    }
    return status_colors.get(status, 'secondary')


@register.filter
def read_time(minutes):
    """Convert minutes to human-readable read time."""
    if minutes < 1:
        return "Less than 1 min read"
    elif minutes < 5:
        return f"{int(minutes)} min read"
    elif minutes < 30:
        return f"{int(minutes)} min read"
    elif minutes < 60:
        return f"{int(minutes // 60)} min read"
    else:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        if hours == 1:
            return f"{hours} hour {mins} min read"
        else:
            return f"{hours} hours {mins} min read"


@register.filter
def emoji(reaction_type):
    """Returns emoji for reaction type."""
    emoji_map = {
        'love': '❤️',
        'like': '👍',
        'laugh': '😂',
        'wow': '😮',
        'sad': '😢',
        'angry': '😠',
    }
    return emoji_map.get(reaction_type, '👍')


@register.filter
def user_liked_comment(comment, user):
    """Check if a user has liked a comment."""
    if not user or not user.is_authenticated:
        return False
    
    from django.contrib.contenttypes.models import ContentType
    from apps.interactions.models import Like
    from apps.comments.models import Comment
    
    content_type = ContentType.objects.get_for_model(Comment)
    return Like.objects.filter(
        user=user,
        content_type=content_type,
        object_id=comment.id
    ).exists()
