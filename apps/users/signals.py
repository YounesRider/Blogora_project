"""
Signaux pour gérer l'inscription et la création des profils utilisateurs.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from allauth.account.signals import user_signed_up
from .models import UserProfile

User = get_user_model()


@receiver(user_signed_up)
def handle_user_signup(request, user, **kwargs):
    """
    Gestionnaire appelé lors de l'inscription d'un nouvel utilisateur.
    Crée le profil utilisateur avec les préférences sélectionnées.
    """
    # Créer le profil utilisateur
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Récupérer les catégories préférées depuis le formulaire
    preferred_categories = request.POST.getlist('preferred_categories')
    
    if preferred_categories:
        profile.preferred_categories.set(preferred_categories)
    
    # Ajouter des informations supplémentaires si disponibles
    if hasattr(request, 'POST'):
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.bio = request.POST.get('bio', '')
        user.save()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crée automatiquement un profil utilisateur lors de la création d'un utilisateur.
    """
    if created and not hasattr(instance, '_profile_created'):
        UserProfile.objects.create(user=instance)
        instance._profile_created = True


@receiver(post_save, sender=User)
def create_default_collection(sender, instance, created, **kwargs):
    """
    Crée la collection par défaut 'Saved Posts' pour les nouveaux utilisateurs.
    """
    if created and not hasattr(instance, '_collection_created'):
        from apps.core.models import Collection
        Collection.objects.get_or_create(
            owner=instance,
            name="Saved Posts",
            defaults={
                'description': 'Your default collection for saved articles',
                'is_private': True
            }
        )
        instance._collection_created = True
