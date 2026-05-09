from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from django.contrib import messages
from .models import Notification


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
        context['notification_counts'] = Notification.objects.filter(
            recipient=self.request.user
        ).values('notification_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
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
        from django.template.loader import render_to_string
        html = render_to_string('notifications/partials/notification_item.html', {
            'notification': notification
        })
        return JsonResponse({
            'success': True,
            'html': html,
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
        return JsonResponse({
            'success': True,
            'unread_count': Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).count()
        })
    
    return JsonResponse({'success': True})


@login_required
def notification_dropdown(request):
    """Return HTML for notification dropdown (used in navbar)."""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'content_type').order_by('-created_at')[:5]
    
    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    from django.template.loader import render_to_string
    html = render_to_string('notifications/partials/dropdown.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })
    
    return HttpResponse(html, content_type='text/html')


@login_required
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
    if request.method == 'POST':
        # Update user notification preferences
        user_profile = request.user.profile
        
        # Update notification settings
        user_profile.email_notifications = request.POST.get('email_notifications', 'off') == 'on'
        user_profile.push_notifications = request.POST.get('push_notifications', 'off') == 'on'
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
        'email_notifications': getattr(request.user.profile, 'email_notifications', True),
        'push_notifications': getattr(request.user.profile, 'push_notifications', True)
    }
    
    return render(request, 'notifications/preferences.html', context)
