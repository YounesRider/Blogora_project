"""
Prédiction des recommandations pour un utilisateur donné.
"""
import logging
from pathlib import Path

import joblib
import numpy as np
from django.db import models

logger = logging.getLogger(__name__)
MODEL_PATH = Path(__file__).parent / "model" / "recommender.pkl"

_model_cache = None


def _load_model():
    global _model_cache
    if _model_cache is None:
        if not MODEL_PATH.exists():
            return None
        _model_cache = joblib.load(MODEL_PATH)
    return _model_cache


def get_recommendations(user_id: int, top_k: int = 10, exclude_seen: bool = True) -> list[int]:
    """
    Retourne une liste d'article_ids recommandés pour un utilisateur.
    Stratégies adaptées selon le profil de l'utilisateur.
    """
    from apps.users.models import UserProfile
    from apps.blog.models import Article
    from apps.interactions.models import Like, SavedArticle, ArticleView
    
    model = _load_model()
    
    # Vérifier si l'utilisateur est nouveau (pas d'interactions)
    user_interactions = ArticleView.objects.filter(user_id=user_id).count() + \
                        Like.objects.filter(user_id=user_id).count() + \
                        SavedArticle.objects.filter(user_id=user_id).count()
    
    is_new_user = user_interactions == 0
    
    if is_new_user:
        # Pour les nouveaux utilisateurs : basé sur les préférences de catégories
        logger.info(f"Nouvel utilisateur {user_id} - recommandations basées sur les préférences")
        return _recommendations_for_new_user(user_id, top_k, exclude_seen)
    
    # Pour les utilisateurs existants
    if model is None:
        logger.warning("Modèle non entraîné. Utilisation des préférences ou fallback popularité.")
        # Try preferences-based first, then fallback
        return _recommendations_for_new_user(user_id, top_k, exclude_seen)

    user_idx = model["user_idx"]
    if user_id not in user_idx:
        logger.info(f"Utilisateur {user_id} pas dans le modèle - utilisation des préférences ou fallback")
        return _recommendations_for_new_user(user_id, top_k, exclude_seen)

    # Utiliser le modèle ML entraîné
    i = user_idx[user_id]
    user_vec = model["user_factors"][i]
    scores = model["article_factors"] @ user_vec

    article_ids = model["article_ids"]

    # Add bonus for articles with more comments (engagement indicator)
    from .feature_engineering import compute_article_features
    article_features = compute_article_features()
    comment_bonus = 0.1  # weight for comment count
    for idx, article_id in enumerate(article_ids):
        if article_id in article_features['article_id'].values:
            comment_count = article_features.loc[article_features['article_id'] == article_id, 'comment_count'].values[0]
            scores[idx] += comment_count * comment_bonus

    if exclude_seen:
        seen = _get_seen_article_ids(user_id)
        article_idx_map = model["article_idx"]
        seen_indices = {article_idx_map[aid] for aid in seen if aid in article_idx_map}
        scores[list(seen_indices)] = -np.inf

    top_indices = np.argsort(scores)[::-1][:top_k]
    return [int(article_ids[i]) for i in top_indices]


def _fallback_popular(top_k: int, user_id: int | None = None) -> list[int]:
    """Retourne les articles les plus populaires (likes + vues) comme fallback."""
    from apps.blog.models import Article
    qs = (
        Article.objects
        .filter(status="published")
        .annotate(comment_count=models.Count('comments'))
        .order_by("-view_count", "-comment_count", "-created_at")
    )
    if user_id:
        from apps.interactions.models import ArticleView
        seen = ArticleView.objects.filter(user_id=user_id).values_list("article_id", flat=True)
        qs = qs.exclude(id__in=seen)
    return list(qs.values_list("id", flat=True)[:top_k])


def _recommendations_for_new_user(user_id: int, top_k: int, exclude_seen: bool) -> list[int]:
    """
    Recommandations pour les nouveaux utilisateurs basées sur leurs préférences de catégories.
    """
    from apps.users.models import UserProfile
    from apps.blog.models import Article
    
    try:
        profile = UserProfile.objects.get(user_id=user_id)
        preferred_categories = profile.preferred_categories.all()
        
        if not preferred_categories:
            # Pas de préférences définies, fallback vers articles populaires
            return _fallback_popular(top_k, user_id=user_id if exclude_seen else None)
        
        # Articles dans les catégories préférées, triés par popularité et commentaires
        queryset = Article.objects.filter(
            status='published',
            categories__in=preferred_categories
        ).annotate(
            comment_count=models.Count('comments')
        ).order_by('-view_count', '-comment_count', '-created_at').distinct()
        
        if exclude_seen:
            seen = _get_seen_article_ids(user_id)
            queryset = queryset.exclude(id__in=seen)
        
        recommended = list(queryset.values_list('id', flat=True)[:top_k])
        return recommended
        
    except UserProfile.DoesNotExist:
        return _fallback_popular(top_k, user_id=user_id if exclude_seen else None)


def _get_seen_article_ids(user_id: int) -> set:
    from apps.interactions.models import ArticleView, SavedArticle, Like
    from django.contrib.contenttypes.models import ContentType
    from apps.blog.models import Article

    article_content_type = ContentType.objects.get_for_model(Article)
    viewed = ArticleView.objects.filter(user_id=user_id).values_list("article_id", flat=True)
    saved = SavedArticle.objects.filter(user_id=user_id).values_list("article_id", flat=True)
    liked = Like.objects.filter(
        user_id=user_id,
        content_type=article_content_type,
    ).values_list("object_id", flat=True)
    return set(viewed) | set(saved) | set(liked)
