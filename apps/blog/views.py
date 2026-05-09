"""
Vues de l'application Blog.

Ce module contient les vues principales pour la gestion des articles :
- Liste des articles avec recommandations IA
- Détail d'article avec interactions
- Création/édition/suppression d'articles
- Articles de l'utilisateur connecté

Fonctionnalités intégrées :
- Recommandations personnalisées par IA
- Système d'interactions (likes, réactions, sauvegardes)
- Optimisation des requêtes avec select_related/prefetch_related
- Pagination et mise en cache
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q, Count, F, Sum, Subquery, OuterRef
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from apps.core.mixins import AuthorRequiredMixin, OwnerRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Article
from .forms import ArticleCreateForm, ArticleUpdateForm
from apps.recommendations.predict import get_recommendations


class ArticleListView(ListView):
    """
    Vue principale pour afficher la liste des articles publiés.
    
    Fonctionnalités :
    - Articles paginés (12 par page)
    - Recommandations personnalisées pour utilisateurs connectés
    - Filtres par catégorie et recherche
    - Optimisation des performances avec annotations
    
    Contexte supplémentaire :
    - recommended_articles : 5 recommandations IA si utilisateur connecté
    - popular_articles : 3 articles les plus populaires
    """
    model = Article
    template_name = 'blog/article_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        """
        Construit le queryset des articles avec optimisations et filtres.
        
        Optimisations :
        - select_related : réduit le nombre de requêtes pour author et category
        - prefetch_related : optimise le chargement des tags
        - annotate : ajoute les compteurs de likes/saves pour éviter les requêtes N+1
        
        Filtres applicables :
        - category_slug : filtre par catégorie via URL
        - tag_slug : filtre par tag via URL  
        - q : recherche textuelle dans titre/extrait/contenu
        """
        from apps.interactions.models import Like
        
        article_content_type = ContentType.objects.get_for_model(Article)
        
        # Subquery to count likes for each article
        likes_subquery = Like.objects.filter(
            content_type=article_content_type,
            object_id=OuterRef('pk')
        ).values('object_id').annotate(
            count=Count('id')
        ).values('count')[:1]
        
        queryset = Article.objects.filter(status='published').select_related(
            'author'
        ).prefetch_related('categories', 'tags').annotate(
            like_count=Subquery(likes_subquery, output_field=models.IntegerField()),
            save_count=Count('saves')
        ).order_by('-created_at')

        # Filter by category from URL
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(categories__slug=category_slug)

        # Filter by tag from URL
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        # Text search from GET parameter ?q=term
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Personalized recommendations if user is authenticated
        if self.request.user.is_authenticated:
            try:
                from apps.recommendations.predict import get_recommendations
                recommended_ids = get_recommendations(
                    self.request.user.id, 
                    top_k=5, 
                    exclude_seen=True
                )
                context['recommended_articles'] = Article.objects.filter(
                    id__in=recommended_ids
                ).select_related('author')
            except:
                # Fallback if recommendations fail
                context['recommended_articles'] = Article.objects.none()
        
        # Popular articles (fallback)
        from apps.interactions.models import Like
        
        article_content_type = ContentType.objects.get_for_model(Article)
        
        # Subquery to count likes for each article
        likes_subquery = Like.objects.filter(
            content_type=article_content_type,
            object_id=OuterRef('pk')
        ).values('object_id').annotate(
            count=Count('id')
        ).values('count')[:1]
        
        context['popular_articles'] = Article.objects.filter(
            status='published'
        ).annotate(
            like_count=Subquery(likes_subquery, output_field=models.IntegerField()),
            popularity_score=F('view_count') + Subquery(likes_subquery, output_field=models.IntegerField()) * 3 + Count('saves') * 2
        ).order_by('-popularity_score')[:5]
        
        return context


class ArticleDetailView(DetailView):
    """Détail d'un article avec tracking et recommandations."""
    model = Article
    template_name = 'blog/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return Article.objects.filter(status='published').select_related(
            'author'
        ).prefetch_related('categories', 'tags', 'comments__author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object
        
        # Incrémenter le compteur de vues
        Article.objects.filter(pk=article.pk).update(view_count=F('view_count') + 1)
        
        # Tracker la vue pour les recommandations
        if self.request.user.is_authenticated:
            from apps.interactions.models import ArticleView
            ArticleView.objects.get_or_create(
                user=self.request.user,
                article=article,
                defaults={'reading_duration': 0}
            )
        
        # Similar articles (same category or tags)
        similar_articles = Article.objects.filter(
            status='published'
        ).filter(
            Q(categories__in=article.categories.all()) | 
            Q(tags__in=article.tags.all())
        ).exclude(pk=article.pk).distinct().select_related('author')[:6]
        
        context['similar_articles'] = similar_articles
        
        # Add interaction data
        from apps.interactions.models import Like, SavedArticle, Reaction
        from django.contrib.contenttypes.models import ContentType
        import json
        
        if self.request.user.is_authenticated:
            
            # Get like state and count
            content_type = ContentType.objects.get_for_model(Article)
            liked = Like.objects.filter(
                user=self.request.user,
                content_type=content_type,
                object_id=article.id
            ).exists()
            
            likes_count = Like.objects.filter(
                content_type=content_type,
                object_id=article.id
            ).count()
            
            # Get save state and count
            saved = SavedArticle.objects.filter(
                user=self.request.user,
                article=article
            ).exists()
            
            saves_count = SavedArticle.objects.filter(article=article).count()
            
            # Get reaction data
            reaction_counts = {}
            from apps.interactions.models import Reaction
            for reaction_type in Reaction.ReactionType:
                reaction_counts[reaction_type.value] = Reaction.objects.filter(
                    article=article, 
                    reaction_type=reaction_type.value
                ).count()
            
            user_reactions = list(
                Reaction.objects.filter(article=article, user=self.request.user)
                .values_list('reaction_type', flat=True)
            )
            
            # Add context variables
            context.update({
                'liked': liked,
                'saved': saved,
                'likes_count': likes_count,
                'saves_count': saves_count,
                'reactions_types': [rt.value for rt in Reaction.ReactionType],
                'reactions_json': json.dumps(reaction_counts),
                'user_reactions': json.dumps(user_reactions),
                'reaction_counts': reaction_counts,
            })
        else:
            # Non-authenticated users get default values
            reaction_counts = {}
            for reaction_type in Reaction.ReactionType:
                reaction_counts[reaction_type.value] = Reaction.objects.filter(
                    article=article, 
                    reaction_type=reaction_type.value
                ).count()
            
            context.update({
                'liked': False,
                'saved': False,
                'likes_count': Like.objects.filter(
                    content_type=ContentType.objects.get_for_model(Article),
                    object_id=article.id
                ).count(),
                'saves_count': SavedArticle.objects.filter(article=article).count(),
                'reactions_types': [rt.value for rt in Reaction.ReactionType],
                'reactions_json': json.dumps(reaction_counts),
                'user_reactions': json.dumps([]),
                'reaction_counts': reaction_counts,
            })
        
        return context


class ArticleCreateView(AuthorRequiredMixin, OwnerRequiredMixin, CreateView):
    """Création d'un nouvel article."""
    model = Article
    form_class = ArticleCreateForm
    template_name = 'blog/article_create.html'
    success_url = reverse_lazy('blog:my_articles')
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        # Handle publish/submit for review logic
        if form.cleaned_data['status'] == 'pending_review':
            if self.request.user.profile.auto_publish:
                form.instance.status = 'published'
                messages.success(self.request, 'Your article has been published!')
            else:
                messages.success(self.request, 'Your article has been submitted for review.')
        else:
            messages.success(self.request, 'Your article has been saved as draft.')
        return super().form_valid(form)
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Article'
        context['description'] = 'Write and publish your article on Blogora'
        return context


class ArticleUpdateView(AuthorRequiredMixin, OwnerRequiredMixin, UpdateView):
    """Modification d'un article existant."""
    model = Article
    form_class = ArticleUpdateForm
    template_name = 'blog/article_update.html'
    success_url = reverse_lazy('blog:my_articles')
    
    def get_queryset(self):
        """User can only edit their own articles."""
        return Article.objects.filter(author=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Your article has been updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Article'
        context['description'] = 'Edit your article on Blogora'
        return context


class MyArticlesView(LoginRequiredMixin, ListView):
    """Liste des articles de l'utilisateur connecté."""
    model = Article
    template_name = 'blog/my_articles.html'
    context_object_name = 'articles'
    paginate_by = 12
    
    def get_queryset(self):
        return Article.objects.filter(author=self.request.user).select_related('category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'My Articles'
        context['description'] = 'Manage all your published and draft articles'
        
        # Statistics
        articles = context['articles']
        context['total_articles'] = Article.objects.filter(author=self.request.user).count()
        context['published_articles'] = Article.objects.filter(author=self.request.user, status='published').count()
        context['draft_articles'] = Article.objects.filter(author=self.request.user, status='draft').count()
        context['pending_articles'] = Article.objects.filter(author=self.request.user, status='pending_review').count()
        context['total_views'] = Article.objects.filter(author=self.request.user).aggregate(total=Sum('view_count'))['total'] or 0
        
        return context


class ArticleDeleteView(AuthorRequiredMixin, OwnerRequiredMixin, DeleteView):
    """Suppression d'un article."""
    model = Article
    template_name = 'blog/article_confirm_delete.html'
    success_url = reverse_lazy('blog:my_articles')
    
    def get_queryset(self):
        """User can only delete their own articles."""
        return Article.objects.filter(author=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Your article has been deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Article'
        context['description'] = 'Confirm the deletion of your article'
        return context


def home(request):
    """Home page with recent articles and recommendations."""
    recent_articles = Article.objects.filter(
        status='published'
    ).select_related('author').order_by('-created_at')[:6]
    
    context = {
        'recent_articles': recent_articles,
    }
    
    if request.user.is_authenticated:
        try:
            recommended_ids = get_recommendations(request.user.id, top_k=6, exclude_seen=True)
            context['recommended_articles'] = Article.objects.filter(
                id__in=recommended_ids
            ).select_related('author')
        except:
            # Fallback if recommendations fail
            context['recommended_articles'] = Article.objects.none()
    
    return render(request, 'blog/home.html', context)


@login_required
def preview_article(request):
    """Preview article based on form data."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET requests allowed'}, status=405)
    
    title = request.GET.get('title', '')
    content = request.GET.get('content', '')
    status = request.GET.get('status', 'draft')
    
    # Create a temporary article object for preview with proper methods
    class TempArticle:
        def __init__(self, title, content, status, author, created_at, updated_at):
            self.title = title
            self.content = content
            self.status = status
            self.author = author
            self.created_at = created_at
            self.updated_at = updated_at
        
        def get_status_display(self):
            status_choices = {
                'draft': 'Draft',
                'pending_review': 'Pending Review',
                'published': 'Published',
                'rejected': 'Rejected',
                'archived': 'Archived'
            }
            return status_choices.get(self.status, self.status.title)
        
        def get_read_time(self):
            # Simple estimation based on content length
            word_count = len(self.content.split()) if self.content else 0
            return max(1, word_count // 200)  # Assume 200 words per minute
    
    temp_article = TempArticle(title, content, status, request.user, timezone.now(), timezone.now())
    
    return render(request, 'blog/article_preview.html', {'article': temp_article})
