from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import F, Count, Q
from apps.blog.models import Article
from .models import Reaction, Like, SavedArticle


@login_required
@require_http_methods(["POST"])
def toggle_reaction(request, article_id, reaction_type):
    """Ajoute ou retire une réaction sur un article."""
    article = get_object_or_404(Article, id=article_id, status='published')
    user = request.user
    
    # Vérifier si l'utilisateur a déjà cette réaction
    existing_reaction = Reaction.objects.filter(
        user=user, 
        article=article, 
        reaction_type=reaction_type
    ).first()
    
    if existing_reaction:
        # Retirer la réaction existante
        existing_reaction.delete()
        action = 'removed'
    else:
        # Ajouter la nouvelle réaction
        Reaction.objects.create(
            user=user,
            article=article,
            reaction_type=reaction_type
        )
        action = 'added'
    
    # Calculer les compteurs de réactions
    reaction_counts = {}
    for reaction_choice in Reaction.ReactionType:
        count = Reaction.objects.filter(
            article=article, 
            reaction_type=reaction_choice.value
        ).count()
        reaction_counts[reaction_choice.value] = count
    
    # Vérifier les réactions de l'utilisateur
    user_reactions = Reaction.objects.filter(
        user=user, 
        article=article
    ).values_list('reaction_type', flat=True)
    
    return JsonResponse({
        'success': True,
        'action': action,
        'reaction_type': reaction_type,
        'reaction_counts': reaction_counts,
        'user_reactions': list(user_reactions),
        'total_reactions': sum(reaction_counts.values())
    })


@login_required
@require_http_methods(["POST"])
def toggle_like(request, article_id):
    """Ajoute ou retire un like sur un article."""
    article = get_object_or_404(Article, id=article_id, status='published')
    user = request.user
    
    existing_like = Like.objects.filter(user=user, article=article).first()
    
    if existing_like:
        existing_like.delete()
        action = 'removed'
        liked = False
    else:
        Like.objects.create(user=user, article=article)
        action = 'added'
        liked = True
    
    # Le compteur de likes est calculé dynamiquement, pas besoin de sauvegarder
    
    return JsonResponse({
        'success': True,
        'action': action,
        'liked': liked,
        'like_count': Like.objects.filter(article=article).count()
    })


@login_required
@require_http_methods(["POST"])
def toggle_save(request, article_id):
    """Ajoute ou retire un article des sauvegardés."""
    article = get_object_or_404(Article, id=article_id, status='published')
    user = request.user
    
    existing_save = SavedArticle.objects.filter(user=user, article=article).first()
    
    if existing_save:
        existing_save.delete()
        action = 'removed'
        saved = False
        message = 'Article retiré des sauvegardés'
    else:
        SavedArticle.objects.create(user=user, article=article)
        action = 'added'
        saved = True
        message = 'Article sauvegardé avec succès'
    
    messages.success(request, message)
    
    return JsonResponse({
        'success': True,
        'action': action,
        'saved': saved,
        'save_count': SavedArticle.objects.filter(article=article).count()
    })


def get_article_reactions(request, article_id):
    """Retourne les réactions d'un article pour l'affichage initial."""
    article = get_object_or_404(Article, id=article_id, status='published')
    
    # Calculer les compteurs de réactions
    reaction_counts = {}
    for reaction_choice in Reaction.ReactionType:
        count = Reaction.objects.filter(
            article=article, 
            reaction_type=reaction_choice.value
        ).count()
        reaction_counts[reaction_choice.value] = count
    
    # Vérifier les réactions de l'utilisateur si connecté
    user_reactions = []
    if request.user.is_authenticated:
        user_reactions = Reaction.objects.filter(
            user=request.user, 
            article=article
        ).values_list('reaction_type', flat=True)
    
    # Compter les likes et sauvegardes
    like_count = Like.objects.filter(article=article).count()
    save_count = SavedArticle.objects.filter(article=article).count()
    
    user_liked = False
    user_saved = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(
            user=request.user, 
            article=article
        ).exists()
        user_saved = SavedArticle.objects.filter(
            user=request.user, 
            article=article
        ).exists()
    
    return JsonResponse({
        'reaction_counts': reaction_counts,
        'user_reactions': list(user_reactions),
        'total_reactions': sum(reaction_counts.values()),
        'like_count': like_count,
        'save_count': save_count,
        'user_liked': user_liked,
        'user_saved': user_saved
    })
