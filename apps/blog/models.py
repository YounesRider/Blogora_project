"""
Modèles de l'application Blog.

Ce module contient les modèles principaux pour la gestion des articles de blog,
incluant les fonctionnalités de publication, les métadonnées SEO,
et les statistiques d'engagement.
"""
from django.db import models
from django.utils.html import strip_tags
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.core.models import TimeStampedModel


class Article(TimeStampedModel):
    """
    Modèle principal pour les articles de blog.
    
    Aligné avec le diagramme UML du cahier des charges.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING_REVIEW = 'pending_review', 'Pending Review'
        PUBLISHED = 'published', 'Published'
        REJECTED = 'rejected', 'Rejected'
        ARCHIVED = 'archived', 'Archived'

    author = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="articles",
    )
    likes = GenericRelation("interactions.Like")
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    content = models.TextField(null=True, blank=True, help_text="Article content (can be rich text)")
    cover_image = models.ImageField(
        upload_to="articles/covers/", 
        null=True, 
        blank=True,
        help_text="Article cover image"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    auto_publish = models.BooleanField(
        default=False,
        help_text="If True, article publishes immediately without review"
    )
    view_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Number of times article was viewed"
    )

    # Taxonomy
    categories = models.ManyToManyField(
        "taxonomy.Category", 
        blank=True, 
        related_name="articles"
    )
    tags = models.ManyToManyField(
        "taxonomy.Tag", 
        blank=True, 
        related_name="articles"
    )

    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    class Meta:
        verbose_name = "article"
        verbose_name_plural = "articles"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["author", "status"]),
        ]

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour automatiser plusieurs traitements :
        
        1. Génération automatique du slug unique à partir du titre
        2. Calcul du temps de lecture estimé (basé sur 200 mots/minute)
        """
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = base_slug
            # Garantir l'unicité du slug en ajoutant un suffixe numérique si nécessaire
            n = 1
            while Article.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{n}"
                n += 1

        super().save(*args, **kwargs)
    
    @property
    def reading_time(self):
        """Estimate reading time in minutes (200 words per minute)."""
        content_text = strip_tags(self.content or "")
        word_count = len(content_text.split())
        return max(1, (word_count + 199) // 200)  # Round up

    @property
    def likes_count(self):
        """Get total likes count."""
        return self.likes.count()

    @property
    def saves_count(self):
        """Get total saves count."""
        from apps.interactions.models import SavedArticle
        return SavedArticle.objects.filter(article=self).count()

    @property
    def reactions_types(self):
        """Get list of reaction types for template."""
        from apps.interactions.models import Reaction
        return [choice.value for choice in Reaction.ReactionType]

    @property
    def reaction_counts(self):
        """Get dictionary of reaction counts by type."""
        from apps.interactions.models import Reaction
        return {
            rt.value: Reaction.objects.filter(article=self, reaction_type=rt.value).count()
            for rt in Reaction.ReactionType
        }

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:detail", kwargs={"slug": self.slug})
