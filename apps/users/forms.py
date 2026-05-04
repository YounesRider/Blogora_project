from django import forms
from allauth.account.forms import SignupForm
from apps.taxonomy.models import Category


class CustomSignupForm(SignupForm):
    """Formulaire d'inscription personnalisé avec sélection de catégories."""
    
    first_name = forms.CharField(max_length=30, required=True, label='Prénom')
    last_name = forms.CharField(max_length=30, required=True, label='Nom')
    bio = forms.CharField(widget=forms.Textarea, required=False, label='Bio')
    preferred_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Centres d\'intérêt',
        help_text='Sélectionnez les catégories qui vous intéressent'
    )
    
    field_order = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'bio', 'preferred_categories']
    
    def save(self, request):
        # Sauvegarder l'utilisateur
        user = super().save(request)
        
        # Mettre à jour les champs supplémentaires
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.bio = self.cleaned_data.get('bio', '')
        user.save()
        
        # Créer le profil avec les préférences
        from apps.users.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        preferred_categories = self.cleaned_data.get('preferred_categories')
        if preferred_categories:
            profile.preferred_categories.set(preferred_categories)
        
        return user
