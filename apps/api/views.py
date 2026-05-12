from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.blog.models import Article
from apps.recommendations.predict import get_recommendations
from apps.taxonomy.models import Category
from apps.interactions.models import ArticleView


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def track_reading(request, article_id):
    """Track reading time for an article."""
    try:
        article = get_object_or_404(Article, id=article_id)
        duration = request.data.get('duration', 0)
        
        if not isinstance(duration, (int, float)) or duration < 0:
            return Response(
                {'error': 'Invalid duration'},
                status=400
            )
        
        # Update or create ArticleView record
        article_view, created = ArticleView.objects.get_or_create(
            user=request.user,
            article=article,
            defaults={'reading_duration': duration}
        )
        
        # Update reading duration if already exists
        if not created and duration > 0:
            article_view.reading_duration = max(article_view.reading_duration, duration)
            article_view.save(update_fields=['reading_duration'])
        
        return Response({
            'success': True,
            'message': f'Reading time recorded: {duration}s',
            'article_id': article_id,
            'duration': duration
        })
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=500
        )



@api_view(["GET"])
@permission_classes([AllowAny])
def onboarding_categories(request):
    categories = Category.objects.order_by("name")
    payload = [
        {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
        }
        for category in categories
    ]
    return Response({"results": payload})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_recommendations(request):
    article_ids = get_recommendations(request.user.id, top_k=10, exclude_seen=True)
    articles = (
        Article.objects.filter(id__in=article_ids, status="published")
        .select_related("author")
        .prefetch_related("categories")
    )
    payload = [
        {
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "excerpt": (article.content or "")[:180],
            "categories": [category.name for category in article.categories.all()],
        }
        for article in articles
    ]
    return Response({"results": payload})
