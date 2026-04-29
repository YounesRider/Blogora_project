from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from apps.core.models import PublishableModel


class Article(PublishableModel):
    """Article de blog principal."""

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
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = base_slug
            # Garantir l'unicité
            n = 1
            while Article.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{n}"
                n += 1

        # Calcul approximatif du temps de lecture (200 mots/min)
        word_count = len(self.body.split())
        self.read_time = max(1, round(word_count / 200))

        if not self.excerpt and self.body:
            self.excerpt = " ".join(self.body.split()[:50]) + "…"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:detail", kwargs={"slug": self.slug})
