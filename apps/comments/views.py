from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Comment
from apps.blog.models import Article


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
    """Supprimer son propre commentaire."""
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)
    
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
