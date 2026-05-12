from apps.blog.models import Article


def navbar_counts(request):
    if not request.user.is_authenticated:
        return {"navbar_counts": {}}

    user_articles = Article.objects.filter(author=request.user)
    return {
        "navbar_counts": {
            "total": user_articles.count(),
            "draft": user_articles.filter(status="draft").count(),
            "pending_review": user_articles.filter(status="pending_review").count(),
        }
    }
