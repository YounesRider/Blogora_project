"""
Prédiction des recommandations pour un utilisateur donné.
"""
import logging
from pathlib import Path

import joblib
import numpy as np

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
    Fallback : articles populaires si l'utilisateur n'est pas dans le modèle.
    """
    model = _load_model()

    if model is None:
        logger.warning("Modèle non entraîné. Fallback popularité.")
        return _fallback_popular(top_k)

    user_idx = model["user_idx"]
    if user_id not in user_idx:
        return _fallback_popular(top_k, user_id=user_id if exclude_seen else None)

    i = user_idx[user_id]
    user_vec = model["user_factors"][i]
    scores = model["article_factors"] @ user_vec

    article_ids = model["article_ids"]

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
        .order_by("-view_count", "-published_at")
    )
    if user_id:
        from apps.interactions.models import ArticleView
        seen = ArticleView.objects.filter(user_id=user_id).values_list("article_id", flat=True)
        qs = qs.exclude(id__in=seen)
    return list(qs.values_list("id", flat=True)[:top_k])


def _get_seen_article_ids(user_id: int) -> set:
    from apps.interactions.models import ArticleView
    return set(
        ArticleView.objects
        .filter(user_id=user_id)
        .values_list("article_id", flat=True)
    )
