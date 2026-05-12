from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import User, UserProfile, Follow
from apps.blog.models import Article
from apps.interactions.models import Like, SavedArticle, ArticleView
from apps.taxonomy.models import Category


@login_required
def profile_view(request):
    """Vue du profil utilisateur avec statistiques."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Statistiques de l'utilisateur
    user_stats = {
        'articles_count': Article.objects.filter(author=request.user).count(),
        'likes_count': Like.objects.filter(user=request.user).count(),
        'saves_count': SavedArticle.objects.filter(user=request.user).count(),
        'views_count': ArticleView.objects.filter(user=request.user).count(),
    }
    
    # Articles récents de l'utilisateur
    user_articles = Article.objects.filter(
        author=request.user
    ).prefetch_related('categories').order_by('-created_at')[:5]
    
    # Articles aimés récemment
    liked_articles = Article.objects.filter(
        likes__user=request.user
    ).select_related('author').prefetch_related('categories').order_by('-likes__created_at')[:5]
    
    # Articles sauvegardés
    saved_articles = Article.objects.filter(
        saves__user=request.user
    ).select_related('author').prefetch_related('categories').order_by('-saves__created_at')[:5]
    
    context = {
        'profile': profile,
        'stats': user_stats,
        'user_articles': user_articles,
        'liked_articles': liked_articles,
        'saved_articles': saved_articles,
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def edit_profile(request):
    """Édition du profil utilisateur."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Mise à jour du profil utilisateur
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        profile.bio = request.POST.get('bio', '')
        
        # Mise à jour du profil étendu
        profile.website = request.POST.get('website', '')
        profile.twitter = request.POST.get('twitter', '')
        profile.github = request.POST.get('github', '')
        profile.location = request.POST.get('location', '')
        
        # Gestion de l'avatar
        if 'avatar' in request.FILES:
            request.user.avatar = request.FILES['avatar']
        
        # Sauvegarde
        request.user.save()
        profile.save()
        
        # Mise à jour des préférences
        category_ids = request.POST.getlist('preferred_categories')
        tag_ids = request.POST.getlist('preferred_tags')
        
        profile.preferred_categories.set(category_ids)
        profile.preferred_tags.set(tag_ids)
        
        messages.success(request, 'Profil mis à jour avec succès !')
        return redirect('users:profile')
    
    # Préférences disponibles
    from apps.taxonomy.models import Category, Tag
    
    # Préparer les catégories avec leur état de sélection
    categories_with_status = []
    for category in Category.objects.all():
        is_selected = category in profile.preferred_categories.all()
        categories_with_status.append({
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'description': category.description,
            'is_selected': is_selected
        })
    
    # Préparer les tags avec leur état de sélection
    tags_with_status = []
    for tag in Tag.objects.all():
        is_selected = tag in profile.preferred_tags.all()
        tags_with_status.append({
            'id': tag.id,
            'name': tag.name,
            'slug': tag.slug,
            'is_selected': is_selected
        })
    
    context = {
        'profile': profile,
        'categories': categories_with_status,
        'tags': tags_with_status,
    }
    
    return render(request, 'users/edit_profile.html', context)


def signup_view(request):
    """Vue d'inscription personnalisée avec sélection de catégories."""
    from apps.taxonomy.models import Category
    
    # Toujours ajouter les catégories au contexte
    categories = Category.objects.all()
    
    if request.method == 'GET':
        return render(request, 'account/signup.html', {'categories': categories})
    
    # Pour POST, utiliser la vue allauth mais avec les catégories
    from allauth.account.views import SignupView
    signup_view_class = SignupView.as_view()
    
    # Créer une requête modifiée pour inclure les catégories
    class ModifiedRequest:
        def __init__(self, original_request):
            self.original_request = original_request
        
        def __getattr__(self, name):
            return getattr(self.original_request, name)
    
    # Utiliser la vue signup avec notre contexte
    response = signup_view_class(request)
    # Si c'est une réponse de formulaire (GET après POST échoué), ajouter les catégories
    if response.status_code == 200 and hasattr(response, 'context_data'):
        response.context_data['categories'] = categories
    
    return response


@login_required
@require_http_methods(["POST"])
def follow_user(request, user_id):
    """Follow or unfollow a user using HTMX."""
    user_to_follow = get_object_or_404(User, pk=user_id)
    
    if user_to_follow == request.user:
        return JsonResponse({'error': 'You cannot follow yourself.'}, status=400)
    
    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=user_to_follow
    )
    
    if created:
        message = f"You are now following {user_to_follow.username}"
        following = True
    else:
        follow.delete()
        message = f"You have unfollowed {user_to_follow.username}"
        following = False
    
    # Return HTMX response
    if request.headers.get('HX-Request'):
        from django.template.loader import render_to_string
        html = render_to_string('users/partials/follow_button.html', {
            'user': user_to_follow,
            'following': following
        })
        return JsonResponse({
            'html': html,
            'message': message,
            'following': following,
            'followers_count': user_to_follow.followers.count()
        })
    
    return JsonResponse({'success': True, 'message': message})


class FollowingListView(LoginRequiredMixin, ListView):
    """List of users that the current user follows."""
    model = Follow
    template_name = 'users/following.html'
    context_object_name = 'follows'
    paginate_by = 20

    def get_queryset(self):
        return Follow.objects.filter(
            follower=self.request.user
        ).select_related('following').order_by('-created_at')


class FollowersListView(LoginRequiredMixin, ListView):
    """List of users that follow the current user."""
    model = Follow
    template_name = 'users/followers.html'
    context_object_name = 'follows'
    paginate_by = 20

    def get_queryset(self):
        return Follow.objects.filter(
            following=self.request.user
        ).select_related('follower').order_by('-created_at')


@login_required
def user_profile(request, username):
    """View another user's profile."""
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(UserProfile, user=user)
    
    # Check if current user follows this user
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=user
        ).exists()
    
    # Get user's articles
    articles = Article.objects.filter(
        author=user,
        status='published'
    ).select_related('author').order_by('-created_at')
    
    context = {
        'profile_user': user,
        'profile': profile,
        'articles': articles,
        'is_following': is_following,
        'followers_count': user.followers.count(),
        'following_count': user.following.count()
    }
    
    return render(request, 'users/user_profile.html', context)


@login_required
def logout_view(request):
    """Custom styled logout view."""
    from django.contrib.auth import logout
    logout(request)
    return render(request, 'account/logout.html')
