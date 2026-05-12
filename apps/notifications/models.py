from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.core.models import TimeStampedModel


class Notification(TimeStampedModel):
    """
    Notification model for user notifications.
    """
    class Type(models.TextChoices):
        COMMENT = 'comment', 'New Comment'
        REPLY = 'reply', 'Reply to Comment'
        LIKE = 'like', 'Like'
        FOLLOW = 'follow', 'New Follower'
        ARTICLE_SUBMITTED = 'article_submitted', 'Review Requested'
        ARTICLE_APPROVED = 'article_approved', 'Article Approved'
        ARTICLE_REJECTED = 'article_rejected', 'Article Rejected'
        ARTICLE_SAVED = 'article_saved', 'Article Saved'
        MODERATOR_CREATED = 'moderator_created', 'Moderator Created'
        MODERATOR_ACTION = 'moderator_action', 'Moderator Action'

    recipient = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    sender = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sent_notifications"
    )
    notification_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        db_index=True
    )
    message = models.TextField()
    is_read = models.BooleanField(
        default=False,
        db_index=True
    )
    
    # Generic foreign key for related objects
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = "notification"
        verbose_name_plural = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "created_at"]),
            models.Index(fields=["notification_type", "created_at"]),
        ]

    def __str__(self):
        return f"Notification for {self.recipient}: {self.get_notification_type_display()}"
