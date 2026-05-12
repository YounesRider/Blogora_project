from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count, OuterRef
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .models import RecommendationScore
from apps.blog.models import Article
from apps.users.models import User


def get_recommendations(user_id, top_k=10, exclude_seen=True):
    """
    Get article recommendations for a user.
    Falls back to coldstart recommendations if no ML scores available.
    
    Args:
        user_id: User ID to get recommendations for
        top_k: Number of recommendations to return
        exclude_seen: Whether to exclude articles the user has already interacted with
    
    Returns:
        List of article IDs
    """
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return []
    
    # Get pre-calculated recommendation scores
    recommendations = RecommendationScore.objects.filter(
        user=user
    ).select_related('article').order_by('-score')[:top_k * 2]  # Get more to filter
    
    # If we have ML scores, use them
    if recommendations.exists():
        # Filter out articles the user has already seen/liked/saved
        if exclude_seen:
            seen_articles = set()
            
            # Articles the user has written
            seen_articles.update(Article.objects.filter(author=user).values_list('id', flat=True))
            
            # Articles the user has liked
            from apps.interactions.models import Like
            from django.contrib.contenttypes.models import ContentType
            article_content_type = ContentType.objects.get_for_model(Article)
            seen_articles.update(
                Like.objects.filter(
                    user=user,
                    content_type=article_content_type
                ).values_list('object_id', flat=True)
            )
            
            # Articles the user has saved (in collections)
            from apps.core.models import Collection
            saved_articles = Article.objects.filter(
                collections__owner=user
            ).values_list('id', flat=True)
            seen_articles.update(saved_articles)
            
            # Filter recommendations
            article_ids = []
            for rec in recommendations:
                if rec.article.id not in seen_articles:
                    article_ids.append(rec.article.id)
                    if len(article_ids) >= top_k:
                        break
        else:
            article_ids = [rec.article.id for rec in recommendations[:top_k]]
        
        if article_ids:
            return article_ids
    
    # No ML scores - use coldstart algorithm
    from .predict import get_recommendations as get_coldstart_recommendations
    return get_coldstart_recommendations(user_id, top_k, exclude_seen)


@login_required
def recommendation_dashboard(request):
    """View personalized recommendations for the user."""
    user = request.user
    
    # Get recommended articles
    recommended_ids = get_recommendations(user.id, top_k=20, exclude_seen=True)
    
    # If we have recommendations, show them in the order they were returned
    if recommended_ids:
        recommended_articles = Article.objects.filter(
            id__in=recommended_ids
        ).select_related('author').prefetch_related('categories')
        
        # Manually order by the recommendation_ids order
        recommended_articles = sorted(
            recommended_articles,
            key=lambda x: recommended_ids.index(x.id) if x.id in recommended_ids else float('inf')
        )
    else:
        recommended_articles = []
    
    # Paginate results
    paginator = Paginator(recommended_articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get user's recent activity for context
    from apps.interactions.models import Like
    from django.contrib.contenttypes.models import ContentType
    article_content_type = ContentType.objects.get_for_model(Article)
    
    recent_likes = Article.objects.filter(
        likes__user=user,
        likes__content_type=article_content_type
    ).select_related('author').order_by('-likes__created_at')[:5]
    
    # Get trending articles (fallback)
    trending_articles = Article.objects.filter(
        status='published'
    ).annotate(
        like_count=Count('likes'),
        comment_count=Count('comments')
    ).order_by('-like_count', '-comment_count')[:10]
    
    # Get liked/saved state for articles on this page
    from apps.interactions.models import SavedArticle
    page_articles = page_obj.object_list if page_obj else []
    article_ids = [a.id for a in page_articles]
    
    liked_article_ids = set()
    saved_article_ids = set()
    if article_ids:
        liked_article_ids = set(
            Like.objects.filter(
                user=user,
                content_type=article_content_type,
                object_id__in=article_ids
            ).values_list('object_id', flat=True)
        )
        saved_article_ids = set(
            SavedArticle.objects.filter(
                user=user,
                article__pk__in=article_ids
            ).values_list('article_id', flat=True)
        )
    
    # Add like/save counts to articles
    for article in page_articles:
        if not hasattr(article, 'like_count'):
            article.like_count = Like.objects.filter(
                content_type=article_content_type,
                object_id=article.id
            ).count()
        if not hasattr(article, 'save_count'):
            article.save_count = SavedArticle.objects.filter(
                article=article
            ).count()
    
    context = {
        'page_obj': page_obj,
        'recent_likes': recent_likes,
        'trending_articles': trending_articles,
        'has_recommendations': len(recommended_ids) > 0,
        'user_liked_article_ids': liked_article_ids,
        'user_saved_article_ids': saved_article_ids
    }
    
    return render(request, 'recommendations/dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def refresh_recommendations(request):
    """Force refresh of recommendations for the current user."""
    try:
        # Trigger recommendation generation (would normally be a Celery task)
        from .management.commands.generate_recommendations import generate_user_recommendations
        generate_user_recommendations(request.user.id)
        
        # Get new recommendations
        recommended_ids = get_recommendations(request.user.id, top_k=10, exclude_seen=True)
        recommended_articles = Article.objects.filter(
            id__in=recommended_ids
        ).select_related('author')
        
        # Return updated HTML
        from django.template.loader import render_to_string
        html = render_to_string('recommendations/partials/article_list.html', {
            'articles': recommended_articles
        })
        
        return JsonResponse({
            'success': True,
            'html': html,
            'message': 'Recommendations refreshed successfully!',
            'count': len(recommended_articles)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Failed to refresh recommendations'
        })


@login_required
def recommendation_settings(request):
    """View and manage recommendation preferences."""
    if request.method == 'POST':
        # Update user preferences
        user_profile = request.user.profile
        
        # Update recommendation preferences
        user_profile.recommendation_enabled = request.POST.get('recommendation_enabled', 'off') == 'on'
        user_profile.save()
        
        from django.contrib import messages
        messages.success(request, 'Preferences updated successfully!')
        return redirect('recommendations:settings')
    
    # Get current recommendation scores count
    score_count = RecommendationScore.objects.filter(user=request.user).count()
    
    context = {
        'score_count': score_count,
        'recommendation_enabled': getattr(request.user.profile, 'recommendation_enabled', True)
    }
    
    return render(request, 'recommendations/settings.html', context)


def get_article_recommendations(request, article_id):
    """Get articles similar to a given article."""
    article = get_object_or_404(Article, pk=article_id, status='published')
    
    # Find users who liked this article
    from apps.interactions.models import Like
    from django.contrib.contenttypes.models import ContentType
    article_content_type = ContentType.objects.get_for_model(Article)
    
    users_who_liked = Like.objects.filter(
        content_type=article_content_type,
        object_id=article.id
    ).values_list('user_id', flat=True)
    
    # Get other articles liked by these users
    similar_articles = Article.objects.filter(
        likes__user_id__in=users_who_liked,
        likes__content_type=article_content_type
    ).exclude(pk=article.id).annotate(
        similarity_score=Count('likes')
    ).order_by('-similarity_score')[:10]
    
    return render(request, 'recommendations/similar_articles.html', {
        'article': article,
        'similar_articles': similar_articles
    })
