from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from django.contrib import messages
from .models import Notification
from apps.users.models import UserProfile


class NotificationListView(LoginRequiredMixin, ListView):
    """List all notifications for the current user."""
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related('sender', 'content_type').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get unread count
        context['unread_count'] = Notification.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).count()
        
        # Get notification counts by type
        notification_counts = Notification.objects.filter(
            recipient=self.request.user
        ).values('notification_type').annotate(
            count=Count('id')
        ).order_by('-count')

        context['notification_counts'] = [
            {
                'notification_type': stat['notification_type'],
                'count': stat['count'],
                'notification_type_display': Notification.Type(stat['notification_type']).label,
            }
            for stat in notification_counts
        ]
        
        return context


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a notification as read using HTMX."""
    notification = get_object_or_404(
        Notification, 
        pk=notification_id, 
        recipient=request.user
    )
    
    notification.is_read = True
    notification.save()
    
    # Return HTMX response
    if request.headers.get('HX-Request'):
        return JsonResponse({
            'success': True,
            'unread_count': Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).count()
        })
    
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Mark all notifications as read."""
    updated_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    if request.headers.get('HX-Request'):
        notifications = Notification.objects.filter(
            recipient=request.user
        ).select_related('sender', 'content_type').order_by('-created_at')[:10]
        unread_count = 0
        from django.template.loader import render_to_string
        from django.middleware.csrf import get_token
        html = render_to_string('notifications/partials/dropdown.html', {
            'notifications': notifications,
            'unread_count': unread_count,
            'recommended_articles': [],
            'csrf_token': get_token(request)
        })
        return HttpResponse(html, content_type='text/html')

    messages.success(request, f'Marked {updated_count} notifications as read.')
    return redirect('notifications:list')


@login_required
@require_http_methods(["POST"])
def delete_notification(request, notification_id):
    """Delete a notification using HTMX."""
    notification = get_object_or_404(
        Notification, 
        pk=notification_id, 
        recipient=request.user
    )
    
    notification.delete()
    
    # Return HTMX response
    if request.headers.get('HX-Request'):
        return HttpResponse('', content_type='text/html')
    
    return JsonResponse({'success': True})


@login_required
def notification_dropdown(request):
    """Return HTML for notification dropdown (used in navbar)."""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'content_type').order_by('-created_at')[:10]
    
    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    recommended_articles = []
    try:
        from apps.recommendations.views import get_recommendations
        from apps.blog.models import Article

        recommended_ids = get_recommendations(request.user.id, top_k=3, exclude_seen=True)
        if recommended_ids:
            recommended_articles = list(Article.objects.filter(
                id__in=recommended_ids,
                status='published'
            ).select_related('author'))
            recommended_articles = sorted(
                recommended_articles,
                key=lambda x: recommended_ids.index(x.id) if x.id in recommended_ids else float('inf')
            )
    except Exception:
        recommended_articles = []

    from django.template.loader import render_to_string
    from django.middleware.csrf import get_token
    html = render_to_string('notifications/partials/dropdown.html', {
        'notifications': notifications,
        'unread_count': unread_count,
        'recommended_articles': recommended_articles,
        'csrf_token': get_token(request)
    })
    
    return HttpResponse(html, content_type='text/html')


def create_notification(recipient, sender, notification_type, message, content_object=None):
    """Helper function to create a notification."""
    return Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        message=message,
        content_object=content_object
    )


@login_required
def notification_preferences(request):
    """View and manage notification preferences."""
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Update user notification preferences
        user_profile.email_notifications = request.POST.get('email_notifications', 'off') == 'on'
        user_profile.push_notifications = request.POST.get('push_notifications', 'off') == 'on'
        user_profile.notify_article_comments = request.POST.get('notify_article_comments', 'off') == 'on'
        user_profile.notify_comment_replies = request.POST.get('notify_comment_replies', 'off') == 'on'
        user_profile.notify_article_likes = request.POST.get('notify_article_likes', 'off') == 'on'
        user_profile.notify_article_saves = request.POST.get('notify_article_saves', 'off') == 'on'
        user_profile.notify_comment_likes = request.POST.get('notify_comment_likes', 'off') == 'on'
        user_profile.save()
        
        messages.success(request, 'Notification preferences updated successfully!')
        return redirect('notifications:preferences')
    
    # Get current notification counts by type for user to manage
    notification_stats = Notification.objects.filter(
        recipient=request.user
    ).values('notification_type').annotate(
        total=Count('id'),
        unread=Count('id', filter=Q(is_read=False))
    ).order_by('-total')
    
    context = {
        'notification_stats': notification_stats,
        'email_notifications': user_profile.email_notifications,
        'push_notifications': user_profile.push_notifications,
        'notify_article_comments': user_profile.notify_article_comments,
        'notify_comment_replies': user_profile.notify_comment_replies,
        'notify_article_likes': user_profile.notify_article_likes,
        'notify_article_saves': user_profile.notify_article_saves,
        'notify_comment_likes': user_profile.notify_comment_likes,
    }
    
    return render(request, 'notifications/preferences.html', context)
