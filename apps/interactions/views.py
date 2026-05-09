from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.contenttypes.models import ContentType
from django.db.models import F, Count, Q
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .models import Like, SavedArticle, Reaction
from apps.blog.models import Article
from apps.comments.models import Comment


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def like_article(request, article_id):
    """Like or unlike an article."""
    article = get_object_or_404(Article, pk=article_id)
    
    # Get or create like
    content_type = ContentType.objects.get_for_model(Article)
    like, created = Like.objects.get_or_create(
        user=request.user,
        content_type=content_type,
        object_id=article.id
    )
    
    if created:
        message = "Article liked!"
        liked = True
    else:
        # Unlike - delete the like
        like.delete()
        message = "Article unliked!"
        liked = False
    
    like_count = Like.objects.filter(
        content_type=content_type,
        object_id=article.id
    ).count()

    return JsonResponse({
        'success': True,
        'message': message,
        'liked': liked,
        'like_count': like_count
    })


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def like_comment(request, comment_id):
    """Like or unlike a comment."""
    comment = get_object_or_404(Comment, pk=comment_id)
    
    # Get or create like
    content_type = ContentType.objects.get_for_model(Comment)
    like, created = Like.objects.get_or_create(
        user=request.user,
        content_type=content_type,
        object_id=comment.id
    )
    
    if created:
        message = "Comment liked!"
        liked = True
    else:
        # Unlike - delete the like
        like.delete()
        message = "Comment unliked!"
        liked = False
    
    like_count = Like.objects.filter(
        content_type=content_type,
        object_id=comment.id
    ).count()

    return JsonResponse({
        'success': True,
        'message': message,
        'liked': liked,
        'like_count': like_count
    })


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def save_article(request, article_id):
    """Save or unsave an article."""
    article = get_object_or_404(Article, pk=article_id)
    
    saved_article, created = SavedArticle.objects.get_or_create(
        user=request.user,
        article=article
    )
    
    if created:
        message = "Article saved!"
        saved = True
    else:
        # Unsave - delete the saved article
        saved_article.delete()
        message = "Article unsaved!"
        saved = False
    
    save_count = SavedArticle.objects.filter(article=article).count()

    return JsonResponse({
        'success': True,
        'message': message,
        'saved': saved,
        'save_count': save_count
    })


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def toggle_reaction(request, article_id, reaction_type):
    """Toggle a reaction emoji on an article."""
    article = get_object_or_404(Article, pk=article_id)
    
    # Validate reaction type
    valid_reactions = [choice.value for choice in Reaction.ReactionType]
    if reaction_type not in valid_reactions:
        return JsonResponse({'success': False, 'error': 'Invalid reaction type.'}, status=400)

    reaction, created = Reaction.objects.get_or_create(
        user=request.user,
        article=article,
        reaction_type=reaction_type
    )

    if not created:
        reaction.delete()
        message = 'Reaction removed.'
        user_reactions = list(
            Reaction.objects.filter(article=article, user=request.user)
            .values_list('reaction_type', flat=True)
        )
    else:
        message = 'Reaction added.'
        user_reactions = [reaction_type]

    reaction_counts = {
        rt.value: Reaction.objects.filter(article=article, reaction_type=rt.value).count()
        for rt in Reaction.ReactionType
    }

    return JsonResponse({
        'success': True,
        'message': message,
        'reaction_counts': reaction_counts,
        'user_reactions': user_reactions,
    })


@login_required
def get_article_reactions(request, article_id):
    """Return current reaction counts and like/save state for the article."""
    article = get_object_or_404(Article, pk=article_id)
    
    # Get like state and count
    content_type = ContentType.objects.get_for_model(Article)
    liked = Like.objects.filter(
        user=request.user,
        content_type=content_type,
        object_id=article.id
    ).exists()
    
    like_count = Like.objects.filter(
        content_type=content_type,
        object_id=article.id
    ).count()
    
    # Get save state and count
    saved = SavedArticle.objects.filter(
        user=request.user,
        article=article
    ).exists()
    
    save_count = SavedArticle.objects.filter(article=article).count()
    
    # Get reaction counts and user reactions
    reaction_counts = {
        rt.value: Reaction.objects.filter(article=article, reaction_type=rt.value).count()
        for rt in Reaction.ReactionType
    }
    
    user_reactions = list(
        Reaction.objects.filter(article=article, user=request.user)
        .values_list('reaction_type', flat=True)
    )

    return JsonResponse({
        'liked': liked,
        'like_count': like_count,
        'saved': saved,
        'save_count': save_count,
        'reaction_counts': reaction_counts,
        'user_reactions': user_reactions,
    })


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def batch_toggle_reaction(request, article_id):
    """Handle multiple reactions at once (remove old one, add new one)."""
    article = get_object_or_404(Article, pk=article_id)
    reaction_type = request.POST.get('reaction_type')
    
    if not reaction_type or reaction_type not in [choice.value for choice in Reaction.ReactionType]:
        return JsonResponse({'success': False, 'error': 'Invalid reaction type.'}, status=400)

    # Remove all existing reactions by this user on this article
    Reaction.objects.filter(user=request.user, article=article).delete()
    
    # Add new reaction
    Reaction.objects.create(
        user=request.user,
        article=article,
        reaction_type=reaction_type
    )
    
    # Get updated counts
    reaction_counts = {
        rt.value: Reaction.objects.filter(article=article, reaction_type=rt.value).count()
        for rt in Reaction.ReactionType
    }
    
    return JsonResponse({
        'success': True,
        'message': 'Reaction updated!',
        'reaction_counts': reaction_counts,
        'user_reactions': [reaction_type],
    })


@login_required
def get_user_likes(request):
    """Get all objects liked by the current user."""
    likes = Like.objects.filter(user=request.user).select_related('content_type')
    
    liked_data = []
    for like in likes:
        if like.content_type.model == 'article':
            liked_data.append({
                'type': 'article',
                'id': like.object_id,
                'created_at': like.created_at.isoformat()
            })
        elif like.content_type.model == 'comment':
            liked_data.append({
                'type': 'comment',
                'id': like.object_id,
                'created_at': like.created_at.isoformat()
            })
    
    return JsonResponse({
        'success': True,
        'likes': liked_data
    })
