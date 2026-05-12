from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimeStampedModel


class User(AbstractUser):
    """
    Utilisateur custom. On étend AbstractUser pour pouvoir
    ajouter des champs sans casser l'auth Django.
    """
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    
    class Role(models.TextChoices):
        GUEST = 'guest', 'Guest'
        USER = 'user', 'User'
        AUTHOR = 'author', 'Author'
        MODERATOR = 'moderator', 'Moderator'
        ADMIN = 'admin', 'Admin'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        help_text="User role in the system"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def profile_picture(self):
        """Get profile picture URL or default."""
        if self.avatar:
            return self.avatar.url
        return None

    @property
    def has_published_articles(self):
        """Check if user has any published articles."""
        return self.articles.filter(status='published').exists()


class UserProfile(TimeStampedModel):
    """
    Profil étendu (1-to-1 avec User).
    Contient les préférences qui alimentent le moteur de recommandation.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True, help_text="Décrivez-vous en quelques mots...")
    social_links = models.JSONField(default=dict, blank=True, help_text="Social media links as JSON")
    website = models.URLField(blank=True)
    twitter = models.CharField(max_length=50, blank=True)
    github = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)
    email_notifications = models.BooleanField(
        default=True,
        help_text="Receive email notifications for important updates"
    )
    push_notifications = models.BooleanField(
        default=True,
        help_text="Receive in-app push notifications"
    )
    notify_article_comments = models.BooleanField(
        default=True,
        help_text="Notify me when someone comments on my article"
    )
    notify_comment_replies = models.BooleanField(
        default=True,
        help_text="Notify me when someone replies to my comment"
    )
    notify_article_likes = models.BooleanField(
        default=True,
        help_text="Notify me when someone likes my article"
    )
    notify_article_saves = models.BooleanField(
        default=True,
        help_text="Notify me when someone saves my article"
    )
    notify_comment_likes = models.BooleanField(
        default=True,
        help_text="Notify me when someone likes my comment"
    )
    auto_publish = models.BooleanField(
        default=False,
        help_text="If True, author's articles are published automatically without review"
    )
    requested_author = models.BooleanField(
        default=False,
        help_text="User has requested to become an author"
    )

    # Préférences pour le moteur IA
    preferred_categories = models.ManyToManyField(
        "taxonomy.Category",
        blank=True,
        related_name="interested_users",
    )
    preferred_tags = models.ManyToManyField(
        "taxonomy.Tag",
        blank=True,
        related_name="interested_users",
    )

    class Meta:
        verbose_name = "profil"

    def __str__(self):
        return f"Profil de {self.user}"
    
    @property
    def is_author(self):
        """Check if user has author role."""
        return self.user.role == User.Role.AUTHOR
    
    @property
    def followers_count(self):
        """Count of users following this user."""
        from apps.users.models import Follow
        return Follow.objects.filter(following=self.user).count()
    
    @property
    def following_count(self):
        """Count of users this user is following."""
        return Follow.objects.filter(follower=self.user).count()


class Follow(TimeStampedModel):
    """
    Follow relationship between users.
    """
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following"
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followers"
    )
    
    class Meta:
        unique_together = ("follower", "following")
        verbose_name = "follow"
        verbose_name_plural = "follows"
        indexes = [
            models.Index(fields=["follower", "created_at"]),
            models.Index(fields=["following", "created_at"]),
        ]
    
    def __str__(self):
        return f"{self.follower} follows {self.following}"
    
    def clean(self):
        """Prevent self-following."""
        if self.follower == self.following:
            from django.core.exceptions import ValidationError
            raise ValidationError("Users cannot follow themselves.")


class Moderator(TimeStampedModel):
    """
    Moderator profile for content moderation.
    Only admins can create and manage moderators.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="moderator_profile",
        help_text="User with moderator role"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="moderators_created",
        help_text="Admin who created this moderator"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this moderator can perform moderation actions"
    )
    
    # Moderation statistics
    articles_reviewed = models.PositiveIntegerField(default=0)
    articles_approved = models.PositiveIntegerField(default=0)
    articles_rejected = models.PositiveIntegerField(default=0)
    comments_deleted = models.PositiveIntegerField(default=0)
    
    # Permissions
    can_review_articles = models.BooleanField(default=True)
    can_delete_articles = models.BooleanField(default=True)
    can_delete_comments = models.BooleanField(default=True)
    can_manage_other_moderators = models.BooleanField(
        default=False,
        help_text="Only senior moderators can manage other moderators"
    )
    
    class Meta:
        verbose_name = "moderator"
        verbose_name_plural = "moderators"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Moderator: {self.user.username}"
    
    def save(self, *args, **kwargs):
        """Ensure moderator user has moderator role and auto_publish on for admins."""
        if self.user.role != User.Role.MODERATOR:
            self.user.role = User.Role.MODERATOR
            self.user.save()
        super().save(*args, **kwargs)
