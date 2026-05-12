import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(__file__).resolve().parent / "datasets"


def setup_django() -> None:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    import django

    django.setup()


def load_score_matrix() -> pd.DataFrame:
    path = DATA_DIR / "user_article_scores.csv"
    if path.exists():
        return pd.read_csv(path)

    raise FileNotFoundError(
        f"Dataset not found. Run export_dataset.py first to create {path}"
    )


def build_indices(df: pd.DataFrame):
    user_ids = sorted(df["user_id"].unique())
    article_ids = sorted(df["article_id"].unique())
    user_idx = {uid: i for i, uid in enumerate(user_ids)}
    article_idx = {aid: i for i, aid in enumerate(article_ids)}
    return user_idx, article_idx


def build_matrix(df: pd.DataFrame, user_idx: dict[int, int], article_idx: dict[int, int]) -> csr_matrix:
    rows = df["user_id"].map(user_idx).values
    cols = df["article_id"].map(article_idx).values
    data = df["score"].values.astype(np.float32)
    return csr_matrix((data, (rows, cols)), shape=(len(user_idx), len(article_idx)))


def train_model(matrix: csr_matrix, n_components: int = 50):
    n_components = min(n_components, min(matrix.shape) - 1)
    model = TruncatedSVD(n_components=n_components, random_state=42)
    user_factors = model.fit_transform(matrix)
    article_factors = model.components_.T
    return user_factors, article_factors


def train_test_split(df: pd.DataFrame):
    df = df.sort_values(["user_id", "score"], ascending=[True, False])
    test_rows = []
    train_rows = []
    for user_id, group in df.groupby("user_id"):
        if len(group) < 2:
            train_rows.append(group)
            continue
        test_rows.append(group.iloc[[0]])
        train_rows.append(group.iloc[1:])
    train_df = pd.concat(train_rows, ignore_index=True)
    test_df = pd.concat(test_rows, ignore_index=True) if test_rows else pd.DataFrame(columns=df.columns)
    return train_df, test_df


def compute_recall_at_k(user_factors, article_factors, user_idx, article_idx, train_df, test_df, k: int = 10):
    article_ids = np.array(sorted(article_idx.keys()))
    inv_article_idx = {v: k for k, v in article_idx.items()}
    hit_count = 0
    total = 0

    train_seen = {}
    for _, row in train_df.iterrows():
        train_seen.setdefault(row["user_id"], set()).add(row["article_id"])

    for _, row in test_df.iterrows():
        user_id = row["user_id"]
        article_id = row["article_id"]
        if user_id not in user_idx or article_id not in article_idx:
            continue

        total += 1
        uidx = user_idx[user_id]
        scores = article_factors.dot(user_factors[uidx])
        seen_ids = train_seen.get(user_id, set())
        seen_indices = [article_idx[aid] for aid in seen_ids if aid in article_idx]
        scores[seen_indices] = -np.inf if seen_indices else scores

        top_indices = np.argsort(scores)[::-1][:k]
        top_article_ids = set(article_ids[top_indices])
        if article_id in top_article_ids:
            hit_count += 1

    recall = float(hit_count) / total if total else 0.0
    return recall, total


def main() -> None:
    setup_django()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading exported score matrix...")
    df = load_score_matrix()
    print(f"Loaded {len(df)} user/article score rows")

    train_df, test_df = train_test_split(df)
    print(f"Training rows: {len(train_df)}, test rows: {len(test_df)}")

    user_idx, article_idx = build_indices(train_df)
    matrix = build_matrix(train_df, user_idx, article_idx)
    print(f"Training matrix shape: {matrix.shape}")

    user_factors, article_factors = train_model(matrix, n_components=20)
    print("Model trained for evaluation")

    recall_at_5, count = compute_recall_at_k(user_factors, article_factors, user_idx, article_idx, train_df, test_df, k=5)
    recall_at_10, _ = compute_recall_at_k(user_factors, article_factors, user_idx, article_idx, train_df, test_df, k=10)

    print(f"Recall@5: {recall_at_5:.4f} on {count} users")
    print(f"Recall@10: {recall_at_10:.4f} on {count} users")

    metrics = {
        "recall_at_5": recall_at_5,
        "recall_at_10": recall_at_10,
        "test_users": int(count),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
    }

    metrics_path = DATA_DIR / "evaluation_metrics.csv"
    pd.DataFrame([metrics]).to_csv(metrics_path, index=False)
    print(f"Saved evaluation metrics to {metrics_path}")


if __name__ == "__main__":
    main()
