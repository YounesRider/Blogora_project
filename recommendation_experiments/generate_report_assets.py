import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(__file__).resolve().parent / "datasets"
OUTPUT_DIR = Path(__file__).resolve().parent / "report_assets"


def setup_django() -> None:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    import django

    django.setup()


def load_dataset(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing dataset file: {path}")
    return pd.read_csv(path)


def plot_event_distribution(interactions: pd.DataFrame) -> Path:
    counts = interactions["event"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 5))
    counts.plot(kind="bar", color=["#4c72b0", "#55a868", "#c44e52"], ax=ax)
    ax.set_title("Interaction Event Distribution")
    ax.set_xlabel("Event Type")
    ax.set_ylabel("Number of Actions")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    output = OUTPUT_DIR / "interaction_event_distribution.png"
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    return output


def plot_top_articles(interactions: pd.DataFrame, articles: pd.DataFrame) -> Path:
    counts = (
        interactions.groupby("article_id")["weight"]
        .count()
        .sort_values(ascending=False)
        .head(10)
    )
    top_articles = articles.set_index("article_id")["title"].reindex(counts.index)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top_articles.values[::-1], counts.values[::-1], color="#4c72b0")
    ax.set_title("Top 10 Articles by Interaction Count")
    ax.set_xlabel("Interactions")
    ax.set_ylabel("Article")
    ax.tick_params(axis="y", labelsize=9)
    output = OUTPUT_DIR / "top_articles_interactions.png"
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    return output


def plot_user_activity(interactions: pd.DataFrame) -> Path:
    user_counts = interactions.groupby("user_id")["weight"].count()
    fig, ax = plt.subplots(figsize=(8, 5))
    user_counts.hist(bins=20, ax=ax, color="#55a868")
    ax.set_title("Distribution of Interactions per User")
    ax.set_xlabel("Interactions per User")
    ax.set_ylabel("Number of Users")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    output = OUTPUT_DIR / "user_activity_distribution.png"
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    return output


def plot_category_distribution(articles: pd.DataFrame) -> Path:
    if "category_ids" not in articles.columns:
        raise ValueError("Article metadata must include category_ids")

    exploded = (
        articles["category_ids"]
        .dropna()
        .astype(str)
        .str.split(",")
        .explode()
    )
    counts = exploded.value_counts().head(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    counts.plot(kind="bar", ax=ax, color="#c44e52")
    ax.set_title("Top 10 Categories by Published Article Count")
    ax.set_xlabel("Category ID")
    ax.set_ylabel("Article Count")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    output = OUTPUT_DIR / "top_categories.png"
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    return output


def export_summary(interactions: pd.DataFrame, articles: pd.DataFrame, users: pd.DataFrame) -> Path:
    summary = {
        "total_interactions": len(interactions),
        "total_users": users["user_id"].nunique() if not users.empty else 0,
        "total_articles": articles["article_id"].nunique() if not articles.empty else 0,
        "unique_event_types": interactions["event"].nunique() if not interactions.empty else 0,
    }
    summary_df = pd.DataFrame([summary])
    output = OUTPUT_DIR / "dataset_summary.csv"
    summary_df.to_csv(output, index=False)
    return output


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    interactions = load_dataset("interactions.csv")
    articles = load_dataset("article_metadata.csv")
    users = load_dataset("user_profiles.csv")

    plots = []
    plots.append(plot_event_distribution(interactions))
    plots.append(plot_top_articles(interactions, articles))
    plots.append(plot_user_activity(interactions))
    plots.append(plot_category_distribution(articles))
    summary_path = export_summary(interactions, articles, users)

    print("Generated report assets:")
    for path in plots:
        print(f" - {path}")
    print(f" - {summary_path}")
    print("Use the generated PNG files and dataset_summary.csv in your report.")


if __name__ == "__main__":
    main()
