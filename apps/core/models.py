"""
Modèles abstraits partagés par toutes les apps.
"""
import uuid
from django.db import models


class TimeStampedModel(models.Model):
    """Ajoute created_at / updated_at à chaque modèle."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Utilise UUID comme clé primaire."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class PublishableModel(TimeStampedModel):
    """
    Modèle pouvant être publié / mis en brouillon / archivé.
    Utilisé par Article et d'autres contenus.
    """
    class Status(models.TextChoices):
        DRAFT = "draft", "Brouillon"
        PUBLISHED = "published", "Publié"
        ARCHIVED = "archived", "Archivé"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def is_published(self) -> bool:
        return self.status == self.Status.PUBLISHED
