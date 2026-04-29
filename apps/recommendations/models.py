"""
Modèles pour le moteur de recommandation.
Stocke les scores calculés pour éviter de recalculer à chaque requête.
"""
from django.db import models
from apps.core.models import TimeStampedModel


class RecommendationScore(TimeStampedModel):
    """
    Score pré-calculé (user, article).
    Mis à jour par la tâche Celery périodique.
    """
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="recommendation_scores",
    )
    article = models.ForeignKey(
        "blog.Article",
        on_delete=models.CASCADE,
        related_name="recommendation_scores",
    )
    score = models.FloatField(default=0.0)
    model_version = models.CharField(max_length=20, default="v1")

    class Meta:
        unique_together = ("user", "article")
        ordering = ["-score"]
        verbose_name = "score de recommandation"

    def __str__(self):
        return f"{self.user} → {self.article} ({self.score:.3f})"
