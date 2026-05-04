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


class UserProfile(TimeStampedModel):
    """
    Profil étendu (1-to-1 avec User).
    Contient les préférences qui alimentent le moteur de recommandation.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True, help_text="Décrivez-vous en quelques mots...")
    website = models.URLField(blank=True)
    twitter = models.CharField(max_length=50, blank=True)
    github = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)

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
