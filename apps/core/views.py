from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count
from .models import Collection
from apps.blog.models import Article


class CollectionListView(LoginRequiredMixin, ListView):
    """List all collections for the current user."""
    model = Collection
    template_name = 'core/collection_list.html'
    context_object_name = 'collections'

    def get_queryset(self):
        return Collection.objects.filter(owner=self.request.user).annotate(
            article_count=Count('articles')
        ).order_by('-created_at')


class CollectionDetailView(LoginRequiredMixin, DetailView):
    """View a collection and its articles."""
    model = Collection
    template_name = 'core/collection_detail.html'
    context_object_name = 'collection'

    def get_queryset(self):
        return Collection.objects.filter(
            owner=self.request.user
        ).prefetch_related('articles')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collection = self.get_object()
        context['articles'] = collection.articles.select_related('author').order_by('-created_at')
        return context


class CollectionCreateView(LoginRequiredMixin, CreateView):
    """Create a new collection."""
    model = Collection
    template_name = 'core/collection_form.html'
    fields = ['name', 'description', 'is_private']
    success_url = reverse_lazy('core:collection_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Collection created successfully!')
        return super().form_valid(form)


class CollectionUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing collection."""
    model = Collection
    template_name = 'core/collection_form.html'
    fields = ['name', 'description', 'is_private']

    def get_queryset(self):
        return Collection.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Collection updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('core:collection_detail', kwargs={'pk': self.object.pk})


class CollectionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a collection."""
    model = Collection
    template_name = 'core/collection_confirm_delete.html'
    success_url = reverse_lazy('core:collection_list')

    def get_queryset(self):
        return Collection.objects.filter(owner=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Collection deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
@require_http_methods(["POST"])
def add_to_collection(request, article_id, collection_id):
    """Add an article to a collection using HTMX."""
    article = get_object_or_404(Article, pk=article_id)
    collection = get_object_or_404(Collection, pk=collection_id, owner=request.user)
    
    if article in collection.articles.all():
        # Remove from collection
        collection.articles.remove(article)
        message = "Article removed from collection"
        in_collection = False
    else:
        # Add to collection
        collection.articles.add(article)
        message = "Article added to collection"
        in_collection = True
    
    # Return HTMX response
    if request.headers.get('HX-Request'):
        from django.template.loader import render_to_string
        html = render_to_string('core/partials/collection_button.html', {
            'article': article,
            'collection': collection,
            'in_collection': in_collection
        })
        return JsonResponse({
            'html': html,
            'message': message,
            'in_collection': in_collection
        })
    
    return JsonResponse({'success': True, 'message': message})


@login_required
def get_user_collections(request, article_id):
    """Get all collections for the current user with article status."""
    article = get_object_or_404(Article, pk=article_id)
    collections = Collection.objects.filter(owner=request.user).annotate(
        article_count=Count('articles')
    ).order_by('-created_at')
    
    # Check which collections contain the article
    article_collections = set(article.collections.values_list('id', flat=True))
    
    collection_data = []
    for collection in collections:
        collection_data.append({
            'id': collection.id,
            'name': collection.name,
            'description': collection.description,
            'article_count': collection.article_count,
            'contains_article': collection.id in article_collections
        })
    
    return JsonResponse({'collections': collection_data})


@login_required
def saved_articles(request):
    """View all saved articles across all collections."""
    collections = Collection.objects.filter(owner=request.user).prefetch_related('articles')
    
    # Get all unique articles from all collections
    articles = []
    seen_articles = set()
    
    for collection in collections:
        for article in collection.articles.all():
            if article.id not in seen_articles:
                articles.append({
                    'article': article,
                    'collections': collection.name
                })
                seen_articles.add(article.id)
    
    return render(request, 'core/saved_articles.html', {
        'articles': articles,
        'collections': collections
    })
