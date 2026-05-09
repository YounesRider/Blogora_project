from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.blog.models import Article
from apps.recommendations.predict import get_recommendations
from apps.taxonomy.models import Category


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
