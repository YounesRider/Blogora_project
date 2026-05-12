from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Comment
from apps.blog.models import Article
from apps.notifications.views import create_notification
from apps.notifications.models import Notification


@login_required
@require_POST
def create_comment(request, article_id):
    """Create a comment on an article."""
    article = get_object_or_404(Article, id=article_id, status='published')
    
    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id')
    
    if not content:
        if request.headers.get('HX-Request'):
            return JsonResponse({'error': 'Comment content cannot be empty.'})
        messages.error(request, 'Comment content cannot be empty.')
        return redirect(article.get_absolute_url())
    
    # Check if it's a reply
    parent = None
    if parent_id:
        parent = get_object_or_404(Comment, id=parent_id, article=article)
    
    comment = Comment.objects.create(
        article=article,
        author=request.user,
        content=content,
        parent=parent
    )

    # Notify the article author about a new top-level comment
    if parent is None and article.author != request.user:
        article_author_profile = getattr(article.author, 'profile', None)
        if getattr(article_author_profile, 'notify_article_comments', True):
            create_notification(
                recipient=article.author,
                sender=request.user,
                notification_type=Notification.Type.COMMENT,
                message=f"{request.user.get_full_name() or request.user.username} commented on your article \"{article.title}\".",
                content_object=comment
            )

    # Notify the parent commenter about a reply
    if parent is not None and parent.author != request.user:
        parent_profile = getattr(parent.author, 'profile', None)
        if getattr(parent_profile, 'notify_comment_replies', True):
            create_notification(
                recipient=parent.author,
                sender=request.user,
                notification_type=Notification.Type.REPLY,
                message=f"{request.user.get_full_name() or request.user.username} replied to your comment: \"{content[:100]}\".",
                content_object=comment
            )
    
    # Return HTMX response
    if request.headers.get('HX-Request'):
        from django.template.loader import render_to_string
        html = render_to_string('comments/partials/comment.html', {
            'comment': comment,
            'user': request.user
        })
        return JsonResponse({
            'success': True,
            'html': html,
            'message': 'Comment posted successfully!'
        })
    
    messages.success(request, 'Your comment has been posted!')
    return redirect(article.get_absolute_url())




@login_required
def delete_comment(request, comment_id):
    """Supprimer son propre commentaire ou un commentaire si l'utilisateur est modérateur."""
    comment = get_object_or_404(Comment, id=comment_id)
    user_can_delete = comment.author == request.user

    if not user_can_delete:
        user_can_delete = (
            request.user.role == 'moderator' and
            getattr(getattr(request.user, 'moderator_profile', None), 'can_delete_comments', False)
        )

    if not user_can_delete:
        messages.error(request, 'Vous n\'avez pas la permission de supprimer ce commentaire.')
        return redirect(comment.article.get_absolute_url())

    if request.method == 'POST':
        article_url = comment.article.get_absolute_url()
        comment.delete()
        messages.success(request, 'Votre commentaire a été supprimé.')
        return redirect(article_url)
    
    return render(request, 'comments/delete_comment.html', {'comment': comment})


@login_required
def edit_comment(request, comment_id):
    """Edit your own comment."""
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if not content:
            messages.error(request, 'Comment content cannot be empty.')
        else:
            comment.content = content
            comment.save()
            
            # Return HTMX response
            if request.headers.get('HX-Request'):
                from django.template.loader import render_to_string
                html = render_to_string('comments/partials/comment_content.html', {
                    'comment': comment,
                    'user': request.user
                })
                return JsonResponse({
                    'success': True,
                    'html': html,
                    'message': 'Comment updated successfully!'
                })
            
            messages.success(request, 'Your comment has been updated.')
            return redirect(comment.get_absolute_url())
    
    return render(request, 'comments/edit_comment.html', {'comment': comment})


def comment_thread(request, comment_id):
    """Afficher un fil de commentaires spécifique."""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Récupérer tous les commentaires du même article pour le contexte
    comments = Comment.objects.filter(
        article=comment.article,
        is_approved=True
    ).select_related('author').order_by('created_at')
    
    return render(request, 'comments/thread.html', {
        'comment': comment,
        'comments': comments,
        'article': comment.article
    })
