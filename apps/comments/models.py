from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
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
        help_text="Comment content (no minimum length)"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies"
    )
    likes = GenericRelation("interactions.Like")
    
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

    @property
    def likes_count(self):
        """Get total likes count using generic likes."""
        return self.likes.count()
    
    def is_liked_by(self, user):
        """Check if comment is liked by a specific user."""
        from django.contrib.contenttypes.models import ContentType
        from apps.interactions.models import Like
        
        if not user or not user.is_authenticated:
            return False
        
        content_type = ContentType.objects.get_for_model(Comment)
        return Like.objects.filter(
            user=user,
            content_type=content_type,
            object_id=self.id
        ).exists()

    def get_absolute_url(self):
        return f"{self.article.get_absolute_url()}#comment-{self.id}"


class CommentLike(TimeStampedModel):
    """Like sur un commentaire."""
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="comment_likes"
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="comment_likes_obj"
    )

    class Meta:
        unique_together = ("comment", "user")
        verbose_name = "like de commentaire"

    def __str__(self):
        return f"{self.user.email} ♥ {self.comment}"
