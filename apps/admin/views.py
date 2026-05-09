from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, UpdateView
from django.db.models import Count, Q, Sum, Subquery, OuterRef
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse_lazy
from apps.core.mixins import AdminRequiredMixin
from apps.blog.models import Article
from apps.users.models import User, Follow
from apps.comments.models import Comment
from apps.interactions.models import Like


class AdminDashboardView(AdminRequiredMixin, LoginRequiredMixin, ListView):
    """Admin dashboard with statistics and pending reviews."""
    template_name = 'admin/dashboard.html'
    context_object_name = None
    paginate_by = None

    def get_queryset(self):
        return None  # We don't need a queryset for this view

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistics
        context['total_users'] = User.objects.count()
        context['total_articles'] = Article.objects.count()
        context['published_articles'] = Article.objects.filter(status='published').count()
        context['draft_articles'] = Article.objects.filter(status='draft').count()
        context['pending_articles'] = Article.objects.filter(status='pending_review').count()
        context['total_comments'] = Comment.objects.count()
        context['total_likes'] = Like.objects.count()
        
        # Recent activity
        context['recent_articles'] = Article.objects.filter(status='published').select_related('author').order_by('-created_at')[:5]
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        context['recent_comments'] = Comment.objects.select_related('author', 'article').order_by('-created_at')[:5]
        
        # Pending reviews (articles needing approval)
        context['pending_reviews'] = Article.objects.filter(
            status='pending_review'
        ).select_related('author').order_by('-created_at')
        
        # Popular articles
        article_content_type = ContentType.objects.get_for_model(Article)
        likes_subquery = Like.objects.filter(
            content_type=article_content_type,
            object_id=OuterRef('pk')
        ).values('object_id').annotate(count=Count('id')).values('count')
        
        context['popular_articles'] = Article.objects.filter(
            status='published'
        ).annotate(
            like_count=Subquery(likes_subquery),
            comment_count=Count('comments')
        ).order_by('-like_count', '-comment_count')[:10]
        
        return context


class AdminUsersView(AdminRequiredMixin, LoginRequiredMixin, ListView):
    """Admin users management view."""
    model = User
    template_name = 'admin/users.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.annotate(
            article_count=Count('articles', distinct=True),
            follower_count=Count('followers', distinct=True),
            following_count=Count('following', distinct=True)
        ).order_by('-date_joined')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Role filter
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['role_filter'] = self.request.GET.get('role', '')
        return context


class AdminUserDetailView(AdminRequiredMixin, LoginRequiredMixin, DetailView):
    """Admin user detail view."""
    model = User
    template_name = 'admin/user_detail.html'
    context_object_name = 'user_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = self.get_object()
        
        # User statistics
        context['article_count'] = Article.objects.filter(author=user_obj).count()
        context['published_articles'] = Article.objects.filter(author=user_obj, status='published').count()
        context['draft_articles'] = Article.objects.filter(author=user_obj, status='draft').count()
        context['pending_articles'] = Article.objects.filter(author=user_obj, status='pending_review').count()
        context['comment_count'] = Comment.objects.filter(author=user_obj).count()
        context['received_likes'] = Like.objects.filter(
            content_type__model='article',
            object_id__in=Article.objects.filter(author=user_obj).values('id')
        ).count()
        
        # User's articles
        context['articles'] = Article.objects.filter(author=user_obj).order_by('-created_at')[:10]
        
        # User's profile
        try:
            context['profile'] = user_obj.profile
        except:
            context['profile'] = None
        
        return context


class AdminArticlesView(AdminRequiredMixin, LoginRequiredMixin, ListView):
    """Admin articles management view."""
    model = Article
    template_name = 'admin/articles.html'
    context_object_name = 'articles'
    paginate_by = 20

    def get_queryset(self):
        queryset = Article.objects.select_related('author').order_by('-created_at')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(author__username__icontains=search)
            )
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class AdminArticleDetailView(AdminRequiredMixin, LoginRequiredMixin, DetailView):
    """Admin article detail view."""
    model = Article
    template_name = 'admin/article_detail.html'
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.get_object()
        
        # Article statistics
        context['like_count'] = Like.objects.filter(
            content_type__model='article',
            object_id=article.id
        ).count()
        context['comment_count'] = Comment.objects.filter(article=article).count()
        context['view_count'] = article.view_count
        
        # Recent comments
        context['comments'] = Comment.objects.filter(
            article=article
        ).select_related('author').order_by('-created_at')
        
        return context


@login_required
def admin_approve_article(request, pk):
    """Approve an article and publish it."""
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to approve articles.')
        return redirect('admin:dashboard')
    
    article = get_object_or_404(Article, pk=pk)
    
    if request.method == 'POST':
        article.status = 'published'
        article.published_at = timezone.now()
        article.save()
        
        messages.success(request, f'Article "{article.title}" has been approved and published.')
        
        # Create notification for author
        from apps.notifications.models import Notification
        Notification.objects.create(
            recipient=article.author,
            sender=request.user,
            notification_type=Notification.Type.ARTICLE_APPROVED,
            message=f'Your article "{article.title}" has been approved and published!',
            content_object=article
        )
        
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        if next_url:
            return redirect(next_url)
    
    return redirect('admin:articles')


@login_required
def admin_reject_article(request, pk):
    """Reject an article."""
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to reject articles.')
        return redirect('admin:dashboard')
    
    article = get_object_or_404(Article, pk=pk)
    
    if request.method == 'POST':
        article.status = 'rejected'
        article.save()
        
        messages.success(request, f'Article "{article.title}" has been rejected.')
        
        # Create notification for author
        from apps.notifications.models import Notification
        Notification.objects.create(
            recipient=article.author,
            sender=request.user,
            notification_type=Notification.Type.ARTICLE_REJECTED,
            message=f'Your article "{article.title}" has been rejected. Please review and resubmit.',
            content_object=article
        )
        
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        if next_url:
            return redirect(next_url)
    
    return redirect('admin:articles')


@login_required
def admin_toggle_user_role(request, pk):
    """Toggle user role between user and author."""
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to change user roles.')
        return redirect('admin:users')
    
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        if user.role == 'user':
            user.role = 'author'
            user.profile.requested_author = False
            user.profile.save()
            messages.success(request, f'{user.username} has been promoted to author.')
        elif user.role == 'author':
            user.role = 'user'
            messages.success(request, f'{user.username} has been demoted to user.')
        
        user.save()
    
    return redirect('admin:user_detail', pk=pk)
