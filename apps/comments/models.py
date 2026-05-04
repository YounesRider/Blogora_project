from django.db import models
from django.core.validators import MinLengthValidator
from apps.core.models import TimeStampedModel


class Comment(TimeStampedModel):
    """Commentaire sur un article."""
    article = models.ForeignKey(
        "blog.Article",
        on_delete=models.CASCADE,
        related_name="comments"
    )
    author = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="comments"
    )
    content = models.TextField(
        validators=[MinLengthValidator(10, message="Le commentaire doit contenir au moins 10 caractères.")]
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies"
    )
    
    # Modération
    is_approved = models.BooleanField(default=True)
    moderated_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderated_comments"
    )
    moderated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "commentaire"
        verbose_name_plural = "commentaires"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["article", "created_at"]),
            models.Index(fields=["author", "created_at"]),
        ]

    def __str__(self):
        return f"Commentaire de {self.author.email} sur {self.article.title[:50]}"

    @property
    def is_reply(self):
        return self.parent is not None

    @property
    def replies_count(self):
        return self.replies.count()

    def get_absolute_url(self):
        return f"{self.article.get_absolute_url()}#comment-{self.id}"


class CommentLike(TimeStampedModel):
    """Like sur un commentaire."""
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="likes"
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="comment_likes"
    )

    class Meta:
        unique_together = ("comment", "user")
        verbose_name = "like de commentaire"

    def __str__(self):
        return f"{self.user.email} ♥ {self.comment}"
