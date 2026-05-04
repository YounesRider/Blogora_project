from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from apps.core.models import TimeStampedModel


class Reaction(TimeStampedModel):
    """Réactions avec emojis sur les articles."""
    
    class ReactionType(models.TextChoices):
        LOVE = 'love', '❤️ Love'
        LIKE = 'like', '👍 Like'
        LAUGH = 'laugh', '😂 Laugh'
        WOW = 'wow', '😮 Wow'
        SAD = 'sad', '😢 Sad'
        ANGRY = 'angry', '😠 Angry'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name='Utilisateur'
    )
    article = models.ForeignKey(
        "blog.Article",
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name='Article'
    )
    reaction_type = models.CharField(
        max_length=20,
        choices=ReactionType.choices,
        verbose_name='Type de réaction'
    )
    
    class Meta:
        verbose_name = 'Réaction'
        verbose_name_plural = 'Réactions'
        unique_together = ['user', 'article', 'reaction_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.get_reaction_type_display()} - {self.article.title}"
    
    @property
    def emoji(self):
        """Retourne l'emoji correspondant au type de réaction."""
        emoji_map = {
            'love': '❤️',
            'like': '👍',
            'laugh': '😂',
            'wow': '😮',
            'sad': '😢',
            'angry': '😠',
        }
        return emoji_map.get(self.reaction_type, '👍')


class Like(TimeStampedModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="likes")
    article = models.ForeignKey("blog.Article", on_delete=models.CASCADE, related_name="likes")

    class Meta:
        unique_together = ("user", "article")
        verbose_name = "j'aime"

    def __str__(self):
        return f"{self.user} ♥ {self.article}"


class SavedArticle(TimeStampedModel):
    """Article sauvegardé / bookmarked."""
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="saved_articles")
    article = models.ForeignKey("blog.Article", on_delete=models.CASCADE, related_name="saves")

    class Meta:
        unique_together = ("user", "article")
        verbose_name = "article sauvegardé"

    def __str__(self):
        return f"{self.user} saved {self.article}"


class ArticleView(TimeStampedModel):
    """
    Enregistre les vues par (user, article).
    Utilisé par le moteur de recommandation comme signal implicite.
    """
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="views",
    )
    article = models.ForeignKey("blog.Article", on_delete=models.CASCADE, related_name="views")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    # Durée de lecture en secondes (via JS)
    reading_duration = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "vue d'article"
        indexes = [
            models.Index(fields=["article", "created_at"]),
        ]
