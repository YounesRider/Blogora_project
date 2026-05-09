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
    Construit la matrice utilisateur×article pour l'entraînement du modèle.
    
    Méthodologie des scores d'interaction implicite :
    - Like : poids 3 (engagement fort)
    - Sauvegarde : poids 2 (intérêt marqué)
    - Vue simple : poids 1 (engagement faible)
    - Durée de lecture : bonus 0.5 par minute (engagement profond)
    
    Cette approche permet de capturer les préférences implicites
    sans nécessiter de notations explicites des utilisateurs.
    
    Returns:
        DataFrame avec colonnes [user_id, article_id, score]
    """
    from apps.interactions.models import Like, SavedArticle, ArticleView

    records = []

    # Collecte des likes (interaction la plus forte)
    for like in Like.objects.select_related("user", "article"):
        records.append({"user_id": like.user_id, "article_id": like.article_id, "value": 3})

    # Collecte des sauvegardes (intérêt moyen)
    for save in SavedArticle.objects.select_related("user", "article"):
        records.append({"user_id": save.user_id, "article_id": save.article_id, "value": 2})

    # Collecte des vues avec bonus de durée de lecture
    for view in ArticleView.objects.filter(user__isnull=False).select_related("user", "article"):
        # Bonus de 0.5 par minute de lecture pour récompenser l'engagement
        reading_bonus = view.reading_duration / 60 * 0.5
        records.append({
            "user_id": view.user_id,
            "article_id": view.article_id,
            "value": 1 + reading_bonus,
        })

    if not records:
        return pd.DataFrame(columns=["user_id", "article_id", "score"])

    # Agrégation des interactions multiples pour le même utilisateur/article
    df = pd.DataFrame(records)
    df = df.groupby(["user_id", "article_id"], as_index=False)["value"].sum()
    # Negative sampling: inject a few unseen items per user with tiny score.
    df = add_negative_samples(df)
    df = df.rename(columns={"value": "score"})
    return df


def add_negative_samples(df: pd.DataFrame, per_user: int = 3) -> pd.DataFrame:
    """Add synthetic low-score interactions for unseen user/article pairs."""
    if df.empty:
        return df

    user_ids = df["user_id"].unique().tolist()
    article_ids = df["article_id"].unique().tolist()
    seen_pairs = set(zip(df["user_id"], df["article_id"]))
    negatives = []

    rng = np.random.default_rng(seed=42)
    for user_id in user_ids:
        unseen = [article_id for article_id in article_ids if (user_id, article_id) not in seen_pairs]
        if not unseen:
            continue
        sampled = rng.choice(unseen, size=min(per_user, len(unseen)), replace=False)
        for article_id in sampled:
            negatives.append({"user_id": user_id, "article_id": article_id, "value": 0.15})

    if negatives:
        df = pd.concat([df, pd.DataFrame(negatives)], ignore_index=True)
    return df


def compute_article_features() -> pd.DataFrame:
    """
    Calcule les features des articles pour le système de recommandation.
    
    Features calculées :
    - Fraîcheur : score exponentiel décroissant basé sur l'âge
    - Popularité : basée sur les interactions (likes, saves, vues)
    - Métadonnées : catégorie, tags, temps de lecture
    
    Returns:
        DataFrame avec les features de chaque article
    """
    from apps.blog.models import Article

    now = timezone.now()
    articles = Article.objects.filter(status="published").prefetch_related("tags")

    rows = []
    for art in articles:
        # Calcul de la fraîcheur (décroissance exponentielle sur 30 jours)
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
    Affinity = somme pondérée des interactions pour les articles de cette catégorie.
    """
    from apps.interactions.models import ArticleView, Like, SavedArticle
    from apps.comments.models import Comment
    from apps.blog.models import Article

    affinity: dict[int, float] = {}
    
    # Pondérations pour différents types d'interactions
    weights = {
        'view': 1.0,
        'like': 3.0,
        'save': 2.0,
        'comment': 4.0,  # Les commentaires sont très indicateurs d'intérêt
        'reading_time': 0.1  # Bonus par minute de lecture
    }
    
    # Vues avec durée de lecture
    viewed = ArticleView.objects.filter(user_id=user_id).select_related("article__category")
    for v in viewed:
        cat = v.article.category_id
        if cat:
            base_score = weights['view'] + (v.reading_duration * weights['reading_time'])
            affinity[cat] = affinity.get(cat, 0) + base_score
    
    # Likes
    liked = Like.objects.filter(user_id=user_id).select_related("article__category")
    for like in liked:
        cat = like.article.category_id
        if cat:
            affinity[cat] = affinity.get(cat, 0) + weights['like']
    
    # Sauvegardes
    saved = SavedArticle.objects.filter(user_id=user_id).select_related("article__category")
    for save in saved:
        cat = save.article.category_id
        if cat:
            affinity[cat] = affinity.get(cat, 0) + weights['save']
    
    # Commentaires (très fort indicateur d'engagement)
    commented = Comment.objects.filter(author_id=user_id).select_related("article__category")
    for comment in commented:
        cat = comment.article.category_id
        if cat:
            # Bonus pour les réponses (engagement plus profond)
            comment_weight = weights['comment'] * (1.5 if comment.parent else 1.0)
            affinity[cat] = affinity.get(cat, 0) + comment_weight
    
    return affinity
