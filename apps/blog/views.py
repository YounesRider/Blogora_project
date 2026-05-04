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
from django.db.models import Q, Count, F, Sum
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
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
        queryset = Article.objects.filter(status='published').select_related(
            'author', 'category'
        ).prefetch_related('tags').annotate(
            like_count=Count('likes'),
            save_count=Count('saves')
        ).order_by('-published_at')

        # Filtre par catégorie depuis l'URL (/category/tech/)
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Filtre par tag depuis l'URL (/tag/python/)
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        # Recherche textuelle depuis le paramètre GET ?q=terme
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(excerpt__icontains=search) |
                Q(body__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Recommandations personnalisées si utilisateur connecté
        if self.request.user.is_authenticated:
            recommended_ids = get_recommendations(
                self.request.user.id, 
                top_k=5, 
                exclude_seen=True
            )
            context['recommended_articles'] = Article.objects.filter(
                id__in=recommended_ids
            ).select_related('author', 'category')
        
        # Articles populaires (fallback)
        context['popular_articles'] = Article.objects.filter(
            status='published'
        ).annotate(
            popularity_score=F('view_count') + Count('likes') * 3 + Count('saves') * 2
        ).order_by('-popularity_score')[:5]
        
        return context


class ArticleDetailView(DetailView):
    """Détail d'un article avec tracking et recommandations."""
    model = Article
    template_name = 'blog/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return Article.objects.filter(status='published').select_related(
            'author', 'category'
        ).prefetch_related('tags', 'comments__author')

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
        
        # Articles similaires (même catégorie ou tags)
        similar_articles = Article.objects.filter(
            status='published'
        ).filter(
            Q(category=article.category) | 
            Q(tags__in=article.tags.all())
        ).exclude(pk=article.pk).distinct().select_related('author', 'category')[:6]
        
        context['similar_articles'] = similar_articles
        return context


class ArticleCreateView(LoginRequiredMixin, CreateView):
    """Création d'un nouvel article."""
    model = Article
    form_class = ArticleCreateForm
    template_name = 'blog/article_create.html'
    success_url = reverse_lazy('blog:my_articles')
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.slug = self.generate_unique_slug(form.cleaned_data['title'])
        messages.success(self.request, 'Votre article a été créé avec succès !')
        return super().form_valid(form)
    
    def generate_unique_slug(self, title):
        """Génère un slug unique à partir du titre."""
        from django.utils.text import slugify
        import uuid
        
        base_slug = slugify(title)
        unique_slug = base_slug
        
        # Vérifier si le slug existe déjà
        counter = 1
        while Article.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1
        
        return unique_slug
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Créer un article'
        context['description'] = 'Rédigez et publiez votre article sur Smart Blog AI'
        return context


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    """Modification d'un article existant."""
    model = Article
    form_class = ArticleUpdateForm
    template_name = 'blog/article_update.html'
    success_url = reverse_lazy('blog:my_articles')
    
    def get_queryset(self):
        """L'utilisateur ne peut modifier que ses propres articles."""
        return Article.objects.filter(author=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Votre article a été mis à jour avec succès !')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier un article'
        context['description'] = 'Modifiez votre article sur Smart Blog AI'
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
        context['title'] = 'Mes articles'
        context['description'] = 'Gérez tous vos articles publiés et brouillons'
        
        # Statistiques
        articles = context['articles']
        context['total_articles'] = Article.objects.filter(author=self.request.user).count()
        context['published_articles'] = Article.objects.filter(author=self.request.user, status='published').count()
        context['draft_articles'] = Article.objects.filter(author=self.request.user, status='draft').count()
        context['total_views'] = Article.objects.filter(author=self.request.user).aggregate(total=Sum('view_count'))['total'] or 0
        
        return context


class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    """Suppression d'un article."""
    model = Article
    template_name = 'blog/article_confirm_delete.html'
    success_url = reverse_lazy('blog:my_articles')
    
    def get_queryset(self):
        """L'utilisateur ne peut supprimer que ses propres articles."""
        return Article.objects.filter(author=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Votre article a été supprimé avec succès !')
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Supprimer un article'
        context['description'] = 'Confirmez la suppression de votre article'
        return context


def home(request):
    """Page d'accueil avec articles récents et recommandations."""
    recent_articles = Article.objects.filter(
        status='published'
    ).select_related('author', 'category').order_by('-published_at')[:6]
    
    context = {
        'recent_articles': recent_articles,
    }
    
    if request.user.is_authenticated:
        recommended_ids = get_recommendations(request.user.id, top_k=6, exclude_seen=True)
        context['recommended_articles'] = Article.objects.filter(
            id__in=recommended_ids
        ).select_related('author', 'category')
    
    return render(request, 'blog/home.html', context)
