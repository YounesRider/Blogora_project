from django import forms
from .models import Article
from apps.taxonomy.models import Category, Tag


class ArticleCreateForm(forms.ModelForm):
    """Article creation form for users."""
    
    class Meta:
        model = Article
        fields = ['title', 'content', 'cover_image', 'categories', 'tags', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your article title...',
                'required': True
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Content of your article...',
                'required': True,
                'id': 'article-content'
            }),
            'categories': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'required': False
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'required': False
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter available categories and tags
        self.fields['categories'].queryset = Category.objects.all()
        self.fields['tags'].queryset = Tag.objects.all()
        
        # Limit status choices for regular users
        if 'status' in self.fields:
            self.fields['status'].choices = [
                ('draft', 'Draft'),
                ('pending_review', 'Submit for Review')
            ]
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters.")
        return title
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 50:
            raise forms.ValidationError("Content must be at least 50 characters.")
        return content


class ArticleUpdateForm(forms.ModelForm):
    """Article update form."""
    
    class Meta:
        model = Article
        fields = ['title', 'content', 'cover_image', 'categories', 'tags', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your article title...',
                'required': True
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Content of your article...',
                'required': True,
                'id': 'article-content'
            }),
            'categories': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'required': False
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'required': False
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categories'].queryset = Category.objects.all()
        self.fields['tags'].queryset = Tag.objects.all()
        
        # Limit status choices for regular users
        if 'status' in self.fields:
            self.fields['status'].choices = [
                ('draft', 'Draft'),
                ('pending_review', 'Submit for Review')
            ]
