from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Comment, CommentLike
from apps.blog.models import Article


@login_required
@require_POST
def create_comment(request, article_id):
    """Créer un commentaire sur un article."""
    article = get_object_or_404(Article, id=article_id, status='published')
    
    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id')
    
    if len(content) < 10:
        messages.error(request, 'Le commentaire doit contenir au moins 10 caractères.')
        return redirect(article.get_absolute_url())
    
    # Vérifier si c'est une réponse
    parent = None
    if parent_id:
        parent = get_object_or_404(Comment, id=parent_id, article=article)
    
    comment = Comment.objects.create(
        article=article,
        author=request.user,
        content=content,
        parent=parent
    )
    
    messages.success(request, 'Votre commentaire a été publié !')
    return redirect(comment.get_absolute_url())


@login_required
@require_POST
def like_comment(request, comment_id):
    """Aimer ou ne plus aimer un commentaire."""
    comment = get_object_or_404(Comment, id=comment_id)
    
    like, created = CommentLike.objects.get_or_create(
        comment=comment,
        user=request.user
    )
    
    if not created:
        # L'utilisateur retirait son like
        like.delete()
        liked = False
    else:
        liked = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'likes_count': comment.likes.count()
        })
    
    return redirect(comment.get_absolute_url())


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
    """Modifier son propre commentaire."""
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if len(content) < 10:
            messages.error(request, 'Le commentaire doit contenir au moins 10 caractères.')
        else:
            comment.content = content
            comment.save()
            messages.success(request, 'Votre commentaire a été modifié.')
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
