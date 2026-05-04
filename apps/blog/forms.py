from django import forms
from .models import Article
from apps.taxonomy.models import Category, Tag


class ArticleCreateForm(forms.ModelForm):
    """Formulaire de création d'article pour les utilisateurs."""
    
    class Meta:
        model = Article
        fields = ['title', 'excerpt', 'body', 'category', 'tags', 'cover', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de votre article...',
                'required': True
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Résumé bref de votre article...',
                'required': True
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Contenu détaillé de votre article...',
                'required': True,
                'id': 'article-content'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'required': False
            }),
            'cover': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les catégories et tags disponibles
        self.fields['category'].queryset = Category.objects.all()
        self.fields['tags'].queryset = Tag.objects.all()
        
        # Limiter les choix de statut pour les utilisateurs normaux
        if 'status' in self.fields:
            self.fields['status'].choices = [
                ('draft', 'Brouillon'),
                ('published', 'Publié')
            ]
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError("Le titre doit contenir au moins 5 caractères.")
        return title
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 50:
            raise forms.ValidationError("Le contenu doit contenir au moins 50 caractères.")
        return content
    
    def clean_excerpt(self):
        excerpt = self.cleaned_data.get('excerpt')
        if len(excerpt) < 10:
            raise forms.ValidationError("Le résumé doit contenir au moins 10 caractères.")
        return excerpt


class ArticleUpdateForm(forms.ModelForm):
    """Formulaire de modification d'article."""
    
    class Meta:
        model = Article
        fields = ['title', 'excerpt', 'body', 'category', 'tags', 'cover', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de votre article...',
                'required': True
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Résumé bref de votre article...',
                'required': True
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Contenu détaillé de votre article...',
                'required': True,
                'id': 'article-content'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'required': False
            }),
            'cover': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['tags'].queryset = Tag.objects.all()
        
        # Limiter les choix de statut pour les utilisateurs normaux
        if 'status' in self.fields:
            self.fields['status'].choices = [
                ('draft', 'Brouillon'),
                ('published', 'Publié')
            ]
