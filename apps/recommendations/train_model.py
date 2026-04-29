"""
Entraînement du modèle de recommandation.
Lance avec : python manage.py shell -c "from apps.recommendations.train_model import train; train()"
Ou via la tâche Celery périodique.
"""
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

from .feature_engineering import build_user_article_matrix

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "model" / "recommender.pkl"
MODEL_PATH.parent.mkdir(exist_ok=True)


def train(n_components: int = 50) -> None:
    """
    Entraîne un modèle de filtrage collaboratif (SVD matricielle).
    Sauvegarde le modèle dans model/recommender.pkl.
    """
    logger.info("Construction de la matrice user×article…")
    df = build_user_article_matrix()

    if df.empty:
        logger.warning("Pas assez de données pour entraîner le modèle.")
        return

    # Encodage des IDs en indices entiers
    user_ids = df["user_id"].unique()
    article_ids = df["article_id"].unique()
    user_idx = {uid: i for i, uid in enumerate(user_ids)}
    article_idx = {aid: i for i, aid in enumerate(article_ids)}

    rows = df["user_id"].map(user_idx).values
    cols = df["article_id"].map(article_idx).values
    data = df["score"].values.astype(np.float32)

    matrix = csr_matrix((data, (rows, cols)), shape=(len(user_ids), len(article_ids)))

    # TruncatedSVD = filtrage collaboratif latent
    n_components = min(n_components, min(matrix.shape) - 1)
    logger.info("Entraînement SVD (n_components=%d)…", n_components)
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    user_factors = svd.fit_transform(matrix)
    article_factors = svd.components_.T

    user_factors_norm = normalize(user_factors)
    article_factors_norm = normalize(article_factors)

    model = {
        "svd": svd,
        "user_factors": user_factors_norm,
        "article_factors": article_factors_norm,
        "user_ids": user_ids,
        "article_ids": article_ids,
        "user_idx": user_idx,
        "article_idx": article_idx,
        "version": "v1",
    }

    joblib.dump(model, MODEL_PATH)
    logger.info("Modèle sauvegardé → %s", MODEL_PATH)
