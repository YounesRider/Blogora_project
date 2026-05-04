"""
Modèles de l'application Blog.

Ce module contient les modèles principaux pour la gestion des articles de blog,
incluant les fonctionnalités de publication, les métadonnées SEO,
et les statistiques d'engagement.
"""
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from apps.core.models import PublishableModel


class Article(PublishableModel):
    """
    Modèle principal pour les articles de blog.
    
    Hérite de PublishableModel qui fournit :
    - status (draft/published)
    - created_at/updated_at
    - published_at
    
    Fonctionnalités principales :
    - Gestion automatique des slugs
    - Métadonnées SEO intégrées
    - Statistiques de lecture
    - Relations avec taxonomie et interactions
    """

    author = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="articles",
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    excerpt = models.TextField(max_length=500, blank=True, help_text="Résumé court affiché dans les listes")
    body = models.TextField()
    cover = models.ImageField(upload_to="covers/articles/", null=True, blank=True)

    # Taxonomy
    category = models.ForeignKey(
        "taxonomy.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    tags = models.ManyToManyField("taxonomy.Tag", blank=True, related_name="articles")

    # Stats (dénormalisées pour les performances)
    view_count = models.PositiveIntegerField(default=0, editable=False)
    read_time = models.PositiveSmallIntegerField(
        default=0,
        editable=False,
        help_text="Temps de lecture estimé en minutes",
    )

    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    # Contrôles
    allow_comments = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = "article"
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["author", "status"]),
        ]

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour automatiser plusieurs traitements :
        
        1. Génération automatique du slug unique à partir du titre
        2. Calcul du temps de lecture estimé (basé sur 200 mots/minute)
        3. Génération automatique de l'extrait si non fourni
        
        Le slug est généré une seule fois lors de la création,
        puis reste inchangé pour préserver les URLs.
        """
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = base_slug
            # Garantir l'unicité du slug en ajoutant un suffixe numérique si nécessaire
            n = 1
            while Article.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{n}"
                n += 1

        # Calcul du temps de lecture (200 mots/min, minimum 1 minute)
        word_count = len(self.body.split())
        self.read_time = max(1, round(word_count / 200))

        # Génération automatique de l'extrait (50 premiers mots)
        if not self.excerpt and self.body:
            self.excerpt = " ".join(self.body.split()[:50]) + "…"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:detail", kwargs={"slug": self.slug})
