from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Tag
from django.db.models import Count

@csrf_exempt
def tag_search(request):
    """API endpoint for tag search with autocomplete."""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'tags': []})
    
    # Search for tags starting with query
    tags = Tag.objects.filter(name__icontains=query).annotate(
        count=Count('articles')
    ).order_by('-count', 'name')[:10]
    
    return JsonResponse({
        'tags': [
            {
                'id': tag.id,
                'name': tag.name,
                'count': tag.count
            }
            for tag in tags
        ]
    })
