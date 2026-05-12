import os
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(__file__).resolve().parent / "datasets"


def setup_django() -> None:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    import django

    django.setup()


def export_interactions() -> pd.DataFrame:
    from apps.interactions.models import ArticleView, Like, SavedArticle

    records = []

    for like in Like.objects.select_related("user", "article").all():
        records.append({
            "user_id": like.user_id,
            "article_id": like.article_id,
            "event": "like",
            "weight": 3.0,
            "timestamp": like.created_at,
        })

    for saved in SavedArticle.objects.select_related("user", "article").all():
        records.append({
            "user_id": saved.user_id,
            "article_id": saved.article_id,
            "event": "save",
            "weight": 2.0,
            "timestamp": saved.created_at,
        })

    for view in ArticleView.objects.filter(user__isnull=False).select_related("user", "article").all():
        reading_bonus = (view.reading_duration or 0) / 60 * 0.5
        records.append({
            "user_id": view.user_id,
            "article_id": view.article_id,
            "event": "view",
            "weight": 1.0 + reading_bonus,
            "timestamp": view.created_at,
        })

    df = pd.DataFrame(records)
    if df.empty:
        df = pd.DataFrame(columns=["user_id", "article_id", "event", "weight", "timestamp"])
    return df


def export_article_metadata() -> pd.DataFrame:
    from apps.blog.models import Article

    rows = []
    for article in Article.objects.filter(status="published").prefetch_related("categories", "tags"):
        rows.append({
            "article_id": article.id,
            "title": article.title,
            "author_id": article.author_id,
            "published_at": article.published_at,
            "created_at": article.created_at,
            "view_count": article.view_count,
            "read_time": article.read_time,
            "cover_image_name": article.cover_image.name if article.cover_image else "",
            "cover_image_url": article.cover_image.url if article.cover_image else "",
            "category_ids": ",".join(str(c.id) for c in article.categories.all()),
            "tag_ids": ",".join(str(t.id) for t in article.tags.all()),
        })
    return pd.DataFrame(rows)


def export_user_profiles() -> pd.DataFrame:
    from apps.users.models import UserProfile

    rows = []
    for profile in UserProfile.objects.select_related("user").prefetch_related("preferred_categories"):
        rows.append({
            "user_id": profile.user_id,
            "username": profile.user.username,
            "preferred_category_ids": ",".join(str(c.id) for c in profile.preferred_categories.all()),
            "preferred_category_names": ",".join(c.name for c in profile.preferred_categories.all()),
            "created_at": profile.created_at if hasattr(profile, "created_at") else None,
        })
    return pd.DataFrame(rows)


def export_score_matrix(interactions: pd.DataFrame) -> pd.DataFrame:
    if interactions.empty:
        return pd.DataFrame(columns=["user_id", "article_id", "score"])

    df = interactions.copy()
    df = df.groupby(["user_id", "article_id"], as_index=False)["weight"].sum()
    df = df.rename(columns={"weight": "score"})
    return df


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Exported {len(df)} rows to {path}")


def main() -> None:
    setup_django()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    interactions = export_interactions()
    write_csv(interactions, DATA_DIR / "interactions.csv")

    articles = export_article_metadata()
    write_csv(articles, DATA_DIR / "article_metadata.csv")

    users = export_user_profiles()
    write_csv(users, DATA_DIR / "user_profiles.csv")

    matrix = export_score_matrix(interactions)
    write_csv(matrix, DATA_DIR / "user_article_scores.csv")

    print("\nData export complete. Use the CSV files in recommendation_experiments/datasets for offline analysis.")


if __name__ == "__main__":
    main()
