from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.contenttypes.models import ContentType
from django.db.models import F
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .models import Like, SavedArticle, Reaction
from apps.blog.models import Article
from apps.comments.models import Comment


@login_required
@require_http_methods(["POST"])
def like_article(request, article_id):
    """Like or unlike an article using HTMX."""
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

    # Return HTMX response
    if request.headers.get('HX-Request'):
        # Return partial template for like button
        from django.template.loader import render_to_string
        html = render_to_string('interactions/partials/like_button.html', {
            'object': article,
            'liked': liked,
            'like_count': like_count,
            'content_type': 'article'
        })
        return JsonResponse({
            'html': html,
            'message': message,
            'liked': liked,
            'like_count': like_count
        })
    
    return JsonResponse({'success': True, 'message': message, 'liked': liked, 'like_count': like_count})


@login_required
@require_http_methods(["POST"])
def like_comment(request, comment_id):
    """Like or unlike a comment using HTMX."""
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

    # Return HTMX response
    if request.headers.get('HX-Request'):
        # Return partial template for like button
        from django.template.loader import render_to_string
        html = render_to_string('interactions/partials/like_button.html', {
            'object': comment,
            'liked': liked,
            'like_count': like_count,
            'content_type': 'comment'
        })
        return JsonResponse({
            'html': html,
            'message': message,
            'liked': liked,
            'like_count': like_count
        })
    
    return JsonResponse({'success': True, 'message': message, 'liked': liked, 'like_count': like_count})


@login_required
def get_user_likes(request):
    """Get all objects liked by the current user."""
    likes = Like.objects.filter(user=request.user).select_related('content_type')
    
    # Group by content type
    articles = []
    comments = []
    
    for like in likes:
        if like.content_type.model == 'article':
            try:
                articles.append(like.content_object)
            except:
                pass
        elif like.content_type.model == 'comment':
            try:
                comments.append(like.content_object)
            except:
                pass
    
    return render(request, 'interactions/user_likes.html', {
        'articles': articles,
        'comments': comments
    })


@login_required
@require_http_methods(["POST"])
def toggle_reaction(request, article_id, reaction_type):
    """Toggle a reaction emoji on an article."""
    article = get_object_or_404(Article, pk=article_id)
    if reaction_type not in [choice.value for choice in Reaction.ReactionType]:
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
    content_type = ContentType.objects.get_for_model(Article)

    like_count = Like.objects.filter(
        content_type=content_type,
        object_id=article.id
    ).count()
    liked = Like.objects.filter(
        user=request.user,
        content_type=content_type,
        object_id=article.id
    ).exists()
    saved = SavedArticle.objects.filter(user=request.user, article=article).exists()
    reaction_counts = {
        rt.value: Reaction.objects.filter(article=article, reaction_type=rt.value).count()
        for rt in Reaction.ReactionType
    }
    user_reactions = list(
        Reaction.objects.filter(article=article, user=request.user)
        .values_list('reaction_type', flat=True)
    )

    return JsonResponse({
        'success': True,
        'like_count': like_count,
        'liked': liked,
        'saved': saved,
        'reaction_counts': reaction_counts,
        'user_reactions': user_reactions,
    })


@login_required
@require_http_methods(["POST"])
def save_article(request, article_id):
    """Save an article to user's default collection."""
    article = get_object_or_404(Article, pk=article_id)
    
    # Get or create default "Saved Posts" collection
    from apps.core.models import Collection
    collection, created = Collection.objects.get_or_create(
        owner=request.user,
        name="Saved Posts",
        defaults={
            'description': 'Your default collection for saved articles',
            'is_private': True
        }
    )
    
    if article in collection.articles.all():
        # Remove from collection
        collection.articles.remove(article)
        message = "Article removed from saved posts"
        saved = False
    else:
        # Add to collection
        collection.articles.add(article)
        message = "Article saved to your collection"
        saved = True
    
    # Return HTMX response
    if request.headers.get('HX-Request'):
        from django.template.loader import render_to_string
        html = render_to_string('interactions/partials/save_button.html', {
            'article': article,
            'saved': saved
        })
        return JsonResponse({
            'html': html,
            'message': message,
            'saved': saved
        })
    
    return JsonResponse({'success': True, 'message': message, 'saved': saved})
