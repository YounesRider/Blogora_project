from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import os
import uuid
from django.conf import settings

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


@require_POST
def upload_inline_image(request):
    """Upload an image for use in article content."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})
    
    if 'image' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No image file provided'})
    
    image_file = request.FILES['image']
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if image_file.content_type not in allowed_types:
        return JsonResponse({'success': False, 'error': 'Unsupported image type'})
    
    # Validate file size (2MB)
    if image_file.size > 2 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': 'Image too large (max 2MB)'})
    
    # Generate unique filename
    ext = os.path.splitext(image_file.name)[1]
    filename = f"{uuid.uuid4()}{ext}"
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'article_images')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, 'wb+') as destination:
        for chunk in image_file.chunks():
            destination.write(chunk)
    
    # Return URL
    image_url = f"{settings.MEDIA_URL}article_images/{filename}"
    return JsonResponse({
        'success': True,
        'url': image_url,
        'filename': filename
    })
