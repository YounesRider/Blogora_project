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
    
    def clean_cover_image(self):
        cover_image = self.cleaned_data.get('cover_image')
        if cover_image:
            # Validate file size (max 5MB)
            if cover_image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image file too large ( > 5MB )")
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']
            if hasattr(cover_image, 'content_type') and cover_image.content_type not in allowed_types:
                raise forms.ValidationError(f"Unsupported image type. Allowed: {', '.join(allowed_types)}")
            
            # Validate file extension as backup
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
            ext = cover_image.name.lower().split('.')[-1] if '.' in cover_image.name else ''
            if f'.{ext}' not in allowed_extensions:
                raise forms.ValidationError(f"Unsupported file extension. Allowed: {', '.join(allowed_extensions)}")
        
        return cover_image


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
    
    def clean_cover_image(self):
        cover_image = self.cleaned_data.get('cover_image')
        if cover_image:
            # Validate file size (max 5MB)
            if cover_image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image file too large ( > 5MB )")
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']
            if hasattr(cover_image, 'content_type') and cover_image.content_type not in allowed_types:
                raise forms.ValidationError(f"Unsupported image type. Allowed: {', '.join(allowed_types)}")
            
            # Validate file extension as backup
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
            ext = cover_image.name.lower().split('.')[-1] if '.' in cover_image.name else ''
            if f'.{ext}' not in allowed_extensions:
                raise forms.ValidationError(f"Unsupported file extension. Allowed: {', '.join(allowed_extensions)}")
        
        return cover_image
