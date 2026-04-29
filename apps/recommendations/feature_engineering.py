"""
Construction des features pour le moteur de recommandation.

Features utilisées :
  - user_article_likes        : 1 si l'user a liké un article similaire
  - user_category_affinity    : fréquence de lecture par catégorie
  - user_tag_overlap          : nb de tags communs entre profil et article
  - article_popularity_score  : (likes + saves*2 + views*0.1) normalisé
  - article_freshness         : score décroissant basé sur l'âge
  - read_ratio                : fraction d'articles lus dans la catégorie
"""
import numpy as np
import pandas as pd
from django.utils import timezone
from datetime import timedelta


def build_user_article_matrix() -> pd.DataFrame:
    """
    Construit la matrice user×article avec un score d'interaction implicite.
    Score = likes*3 + saves*2 + views*1 + (reading_duration/60)*0.5
    """
    from apps.interactions.models import Like, SavedArticle, ArticleView

    records = []

    for like in Like.objects.select_related("user", "article"):
        records.append({"user_id": like.user_id, "article_id": like.article_id, "value": 3})

    for save in SavedArticle.objects.select_related("user", "article"):
        records.append({"user_id": save.user_id, "article_id": save.article_id, "value": 2})

    for view in ArticleView.objects.filter(user__isnull=False).select_related("user", "article"):
        reading_bonus = view.reading_duration / 60 * 0.5
        records.append({
            "user_id": view.user_id,
            "article_id": view.article_id,
            "value": 1 + reading_bonus,
        })

    if not records:
        return pd.DataFrame(columns=["user_id", "article_id", "score"])

    df = pd.DataFrame(records)
    df = df.groupby(["user_id", "article_id"], as_index=False)["value"].sum()
    df = df.rename(columns={"value": "score"})
    return df


def compute_article_features() -> pd.DataFrame:
    """Retourne un DataFrame avec les features par article."""
    from apps.blog.models import Article

    now = timezone.now()
    articles = Article.objects.filter(status="published").prefetch_related("tags")

    rows = []
    for art in articles:
        age_days = (now - (art.published_at or art.created_at)).days
        freshness = np.exp(-age_days / 30)  # décroit exponentiellement sur 30j

        popularity = (
            art.likes.count() * 3
            + art.saves.count() * 2
            + art.view_count * 0.1
        )

        rows.append({
            "article_id": art.id,
            "category_id": art.category_id,
            "freshness": freshness,
            "popularity": popularity,
            "read_time": art.read_time,
        })

    return pd.DataFrame(rows)


def compute_user_category_affinity(user_id: int) -> dict:
    """
    Retourne un dict {category_id: affinity_score} pour un utilisateur.
    Affinity = somme des scores d'interaction pour les articles de cette catégorie.
    """
    from apps.interactions.models import ArticleView
    from apps.blog.models import Article

    viewed = (
        ArticleView.objects
        .filter(user_id=user_id)
        .select_related("article__category")
    )

    affinity: dict[int, float] = {}
    for v in viewed:
        cat = v.article.category_id
        if cat:
            affinity[cat] = affinity.get(cat, 0) + 1 + v.reading_duration / 60 * 0.2

    return affinity
