from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, UpdateView
from django.db.models import Count, Q, Sum, Subquery, OuterRef
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse_lazy
from apps.core.mixins import AdminRequiredMixin, ModeratorRequiredMixin
from apps.blog.models import Article
from apps.users.models import User, Follow, Moderator
from apps.comments.models import Comment
from apps.interactions.models import Like
from apps.notifications.models import Notification


def notify_admins_of_moderator_action(actor, action, article):
    admin_recipients = User.objects.filter(
        Q(is_staff=True) | Q(role='admin')
    ).exclude(pk=actor.pk)
    notifications = [
        Notification(
            recipient=recipient,
            sender=actor,
            notification_type=Notification.Type.MODERATOR_ACTION,
            message=f'{actor.username} {action} the article "{article.title}".',
            content_object=article
        )
        for recipient in admin_recipients
    ]
    if notifications:
        Notification.objects.bulk_create(notifications)


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
def admin_delete_article(request, pk):
    """Delete an article from the admin interface and notify the author."""
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to delete articles.')
        return redirect('admin:dashboard')

    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        title = article.title
        author = article.author
        article.delete()
        messages.success(request, f'Article "{title}" has been deleted.')

        from apps.notifications.models import Notification
        Notification.objects.create(
            recipient=author,
            sender=request.user,
            notification_type=Notification.Type.ARTICLE_REJECTED,
            message=f'Your article "{title}" has been removed by an administrator.',
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


@login_required
def admin_delete_user(request, pk):
    """Delete a user account (admin only)."""
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to delete users.')
        return redirect('admin:users')
    
    user = get_object_or_404(User, pk=pk)
    
    # Prevent deleting self
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('admin:user_detail', pk=pk)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" and all associated data have been deleted.')
        return redirect('admin:users')
    
    return redirect('admin:user_detail', pk=pk)


@login_required
def admin_set_auto_publish(request, pk):
    """Enable or disable auto-publish for an author."""
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to change auto-publish settings.')
        return redirect('admin:users')
    
    user = get_object_or_404(User, pk=pk)
    
    if user.role not in ['author', 'admin']:
        messages.error(request, 'Only authors can have auto-publish enabled.')
        return redirect('admin:user_detail', pk=pk)
    
    if request.method == 'POST':
        profile = user.profile
        profile.auto_publish = not profile.auto_publish
        profile.save()
        
        status = "enabled" if profile.auto_publish else "disabled"
        messages.success(request, f'Auto-publish has been {status} for {user.username}.')
    
    return redirect('admin:user_detail', pk=pk)


# ============================================================================
# MODERATOR MANAGEMENT
# ============================================================================

class AdminModeratorsView(AdminRequiredMixin, LoginRequiredMixin, ListView):
    """List all moderators."""
    template_name = 'admin/moderators.html'
    context_object_name = 'moderators'
    paginate_by = 20

    def get_queryset(self):
        queryset = Moderator.objects.select_related('user', 'created_by').order_by('-created_at')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        # Active filter
        active_only = self.request.GET.get('active_only')
        if active_only == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['active_only'] = self.request.GET.get('active_only', '')
        context['total_moderators'] = Moderator.objects.count()
        context['active_moderators'] = Moderator.objects.filter(is_active=True).count()
        return context


class AdminModeratorDetailView(AdminRequiredMixin, LoginRequiredMixin, DetailView):
    """Admin moderator detail view."""
    model = Moderator
    template_name = 'admin/moderator_detail.html'
    context_object_name = 'moderator'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        moderator = self.get_object()
        context['user_obj'] = moderator.user
        return context


@login_required
def admin_create_moderator(request, pk):
    """Promote a user to moderator role."""
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to create moderators.')
        return redirect('admin:users')
    
    user = get_object_or_404(User, pk=pk)
    
    # Check if already a moderator
    if hasattr(user, 'moderator_profile'):
        messages.warning(request, f'{user.username} is already a moderator.')
        return redirect('admin:user_detail', pk=pk)
    
    if request.method == 'POST':
        try:
            Moderator.objects.create(
                user=user,
                created_by=request.user
            )
            messages.success(request, f'{user.username} has been promoted to moderator.')

            admin_recipients = User.objects.filter(
                Q(is_staff=True) | Q(role='admin')
            ).exclude(pk=request.user.pk)
            notifications = [
                Notification(
                    recipient=recipient,
                    sender=request.user,
                    notification_type=Notification.Type.MODERATOR_CREATED,
                    message=f'{request.user.username} promoted {user.username} to moderator.',
                    content_object=user
                )
                for recipient in admin_recipients
            ]
            if notifications:
                Notification.objects.bulk_create(notifications)
        except Exception as e:
            messages.error(request, f'Error creating moderator: {str(e)}')
    
    return redirect('admin:user_detail', pk=pk)


@login_required
def admin_delete_moderator(request, pk):
    """Demote a moderator back to regular user."""
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to delete moderators.')
        return redirect('admin:moderators')
    
    moderator = get_object_or_404(Moderator, pk=pk)
    user = moderator.user
    
    if request.method == 'POST':
        username = user.username
        user.role = User.Role.USER
        user.save()
        moderator.delete()
        messages.success(request, f'{username} has been demoted to regular user.')
        return redirect('admin:moderators')
    
    return redirect('admin:moderator_detail', pk=pk)


@login_required
def admin_toggle_moderator_permission(request, pk, permission):
    """Toggle a moderator permission."""
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to manage moderators.')
        return redirect('admin:moderators')
    
    moderator = get_object_or_404(Moderator, pk=pk)
    
    if permission == 'review_articles':
        moderator.can_review_articles = not moderator.can_review_articles
    elif permission == 'delete_articles':
        moderator.can_delete_articles = not moderator.can_delete_articles
    elif permission == 'delete_comments':
        moderator.can_delete_comments = not moderator.can_delete_comments
    elif permission == 'manage_moderators':
        moderator.can_manage_other_moderators = not moderator.can_manage_other_moderators
    else:
        messages.error(request, 'Invalid permission.')
        return redirect('admin:moderator_detail', pk=pk)
    
    moderator.save()
    messages.success(request, f'Permission "{permission}" has been toggled.')
    return redirect('admin:moderator_detail', pk=pk)


@login_required
def admin_toggle_moderator_active(request, pk):
    """Activate or deactivate a moderator."""
    if not request.user.is_staff and request.user.role != 'admin':
        messages.error(request, 'You do not have permission to manage moderators.')
        return redirect('admin:moderators')
    
    moderator = get_object_or_404(Moderator, pk=pk)
    
    if request.method == 'POST':
        moderator.is_active = not moderator.is_active
        moderator.save()
        status = "activated" if moderator.is_active else "deactivated"
        messages.success(request, f'Moderator has been {status}.')
    
    return redirect('admin:moderator_detail', pk=pk)


# ============================================================================
# MODERATOR CONTENT REVIEW
# ============================================================================

class ModeratorDashboardView(ModeratorRequiredMixin, LoginRequiredMixin, ListView):
    """Moderator dashboard showing content to review."""
    template_name = 'moderation/dashboard.html'
    context_object_name = None
    paginate_by = None

    def get_queryset(self):
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Pending articles for review
        context['pending_articles'] = Article.objects.filter(
            status='pending_review'
        ).select_related('author').order_by('-created_at')[:10]
        
        # Unapproved comments
        context['unapproved_comments'] = Comment.objects.filter(
            is_approved=False
        ).select_related('author', 'article').order_by('-created_at')[:10]
        
        # Get moderator stats if user is a moderator
        if hasattr(self.request.user, 'moderator_profile'):
            moderator = self.request.user.moderator_profile
            context['articles_reviewed'] = moderator.articles_reviewed
            context['articles_approved'] = moderator.articles_approved
            context['articles_rejected'] = moderator.articles_rejected
            context['comments_deleted'] = moderator.comments_deleted
        
        return context


class ModeratorArticlesView(ModeratorRequiredMixin, LoginRequiredMixin, ListView):
    """Articles pending review for moderators."""
    model = Article
    template_name = 'moderation/articles.html'
    context_object_name = 'articles'
    paginate_by = 20

    def get_queryset(self):
        return Article.objects.filter(
            status='pending_review'
        ).select_related('author').order_by('-created_at')


@login_required
def moderator_approve_article(request, pk):
    """Moderator approves an article."""
    if not (request.user.role in ['moderator', 'admin']):
        messages.error(request, 'You do not have permission to approve articles.')
        return redirect('dashboard')
    
    # Check moderator permissions
    if request.user.role == 'moderator' and hasattr(request.user, 'moderator_profile'):
        if not request.user.moderator_profile.can_review_articles:
            messages.error(request, 'You do not have permission to review articles.')
            return redirect('dashboard')
    
    article = get_object_or_404(Article, pk=pk)
    
    if request.method == 'POST':
        article.status = 'published'
        article.published_at = timezone.now()
        article.save()
        
        # Update moderator stats
        if hasattr(request.user, 'moderator_profile'):
            moderator = request.user.moderator_profile
            moderator.articles_reviewed += 1
            moderator.articles_approved += 1
            moderator.save()
        
        messages.success(request, f'Article "{article.title}" has been approved.')
        
        # Create notification for author
        Notification.objects.create(
            recipient=article.author,
            sender=request.user,
            notification_type=Notification.Type.ARTICLE_APPROVED,
            message=f'Your article "{article.title}" has been approved and published!',
            content_object=article
        )
        notify_admins_of_moderator_action(request.user, 'approved', article)
        
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        if next_url:
            return redirect(next_url)
    
    return redirect('moderation:articles')


@login_required
def moderator_reject_article(request, pk):
    """Moderator rejects an article."""
    if not (request.user.role in ['moderator', 'admin']):
        messages.error(request, 'You do not have permission to reject articles.')
        return redirect('dashboard')
    
    # Check moderator permissions
    if request.user.role == 'moderator' and hasattr(request.user, 'moderator_profile'):
        if not request.user.moderator_profile.can_review_articles:
            messages.error(request, 'You do not have permission to review articles.')
            return redirect('dashboard')
    
    article = get_object_or_404(Article, pk=pk)
    
    if request.method == 'POST':
        article.status = 'rejected'
        article.save()
        
        # Update moderator stats
        if hasattr(request.user, 'moderator_profile'):
            moderator = request.user.moderator_profile
            moderator.articles_reviewed += 1
            moderator.articles_rejected += 1
            moderator.save()
        
        messages.success(request, f'Article "{article.title}" has been rejected.')
        
        # Create notification for author
        Notification.objects.create(
            recipient=article.author,
            sender=request.user,
            notification_type=Notification.Type.ARTICLE_REJECTED,
            message=f'Your article "{article.title}" has been rejected. Please review and resubmit.',
            content_object=article
        )
        notify_admins_of_moderator_action(request.user, 'rejected', article)
        
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        if next_url:
            return redirect(next_url)
    
    return redirect('moderation:articles')


@login_required
def moderator_delete_article(request, pk):
    """Moderator deletes an article permanently."""
    if not (request.user.role in ['moderator', 'admin']):
        messages.error(request, 'You do not have permission to delete articles.')
        return redirect('dashboard')
    
    # Check moderator permissions
    if request.user.role == 'moderator' and hasattr(request.user, 'moderator_profile'):
        if not request.user.moderator_profile.can_delete_articles:
            messages.error(request, 'You do not have permission to delete articles.')
            return redirect('dashboard')
    
    article = get_object_or_404(Article, pk=pk)
    
    if request.method == 'POST':
        title = article.title
        article.delete()
        messages.success(request, f'Article "{title}" has been permanently deleted.')
        return redirect('moderation:articles')
    
    return redirect('moderation:articles')


class ModeratorCommentsView(ModeratorRequiredMixin, LoginRequiredMixin, ListView):
    """Comments pending review for moderators."""
    model = Comment
    template_name = 'moderation/comments.html'
    context_object_name = 'comments'
    paginate_by = 20

    def get_queryset(self):
        return Comment.objects.filter(
            is_approved=False
        ).select_related('author', 'article').order_by('-created_at')


@login_required
def moderator_approve_comment(request, pk):
    """Moderator approves a comment."""
    if not (request.user.role in ['moderator', 'admin']):
        messages.error(request, 'You do not have permission to moderate comments.')
        return redirect('dashboard')
    
    # Check moderator permissions
    if request.user.role == 'moderator' and hasattr(request.user, 'moderator_profile'):
        if not request.user.moderator_profile.can_delete_comments:
            messages.error(request, 'You do not have permission to moderate comments.')
            return redirect('dashboard')
    
    comment = get_object_or_404(Comment, pk=pk)
    
    if request.method == 'POST':
        comment.is_approved = True
        comment.moderated_by = request.user
        comment.moderated_at = timezone.now()
        comment.save()
        
        messages.success(request, 'Comment has been approved.')
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
        if next_url:
            return redirect(next_url)
    
    return redirect('moderation:comments')


@login_required
def moderator_delete_comment(request, pk):
    """Moderator deletes a comment."""
    if not (request.user.role in ['moderator', 'admin']):
        messages.error(request, 'You do not have permission to delete comments.')
        return redirect('dashboard')
    
    # Check moderator permissions
    if request.user.role == 'moderator' and hasattr(request.user, 'moderator_profile'):
        if not request.user.moderator_profile.can_delete_comments:
            messages.error(request, 'You do not have permission to delete comments.')
            return redirect('dashboard')
    
    comment = get_object_or_404(Comment, pk=pk)
    article = comment.article
    
    if request.method == 'POST':
        comment.delete()
        
        # Update moderator stats
        if hasattr(request.user, 'moderator_profile'):
            moderator = request.user.moderator_profile
            moderator.comments_deleted += 1
            moderator.save()
        
        messages.success(request, 'Comment has been deleted.')
        return redirect('admin:moderation_comments')
    
    return redirect('admin:moderation_comments')


# ============================================================================
# BULK MODERATION ACTIONS
# ============================================================================

@login_required
def moderator_bulk_approve_articles(request):
    """Bulk approve multiple articles."""
    if not (request.user.role in ['moderator', 'admin']):
        messages.error(request, 'You do not have permission to approve articles.')
        return redirect('dashboard')
    
    # Check moderator permissions
    if request.user.role == 'moderator' and hasattr(request.user, 'moderator_profile'):
        if not request.user.moderator_profile.can_review_articles:
            messages.error(request, 'You do not have permission to review articles.')
            return redirect('admin:moderation_articles')
    
    if request.method == 'POST':
        article_ids = request.POST.get('article_ids', '').split(',')
        article_ids = [int(id) for id in article_ids if id.strip()]
        
        if not article_ids:
            messages.error(request, 'No articles selected.')
            return redirect('admin:moderation_articles')
        
        articles = Article.objects.filter(pk__in=article_ids, status='pending_review')
        approved_count = 0
        
        for article in articles:
            article.status = 'published'
            article.published_at = timezone.now()
            article.save()
            approved_count += 1
            
            # Create notification for author
            Notification.objects.create(
                recipient=article.author,
                sender=request.user,
                notification_type=Notification.Type.ARTICLE_APPROVED,
                message=f'Your article "{article.title}" has been approved and published!',
                content_object=article
            )
            notify_admins_of_moderator_action(request.user, 'approved', article)
        
        # Update moderator stats
        if hasattr(request.user, 'moderator_profile'):
            moderator = request.user.moderator_profile
            moderator.articles_reviewed += approved_count
            moderator.articles_approved += approved_count
            moderator.save()
        
        messages.success(request, f'{approved_count} article{"s" if approved_count != 1 else ""} approved successfully.')
    
    return redirect('admin:moderation_articles')


@login_required
def moderator_bulk_reject_articles(request):
    """Bulk reject multiple articles."""
    if not (request.user.role in ['moderator', 'admin']):
        messages.error(request, 'You do not have permission to reject articles.')
        return redirect('dashboard')
    
    # Check moderator permissions
    if request.user.role == 'moderator' and hasattr(request.user, 'moderator_profile'):
        if not request.user.moderator_profile.can_review_articles:
            messages.error(request, 'You do not have permission to review articles.')
            return redirect('admin:moderation_articles')
    
    if request.method == 'POST':
        article_ids = request.POST.get('article_ids', '').split(',')
        article_ids = [int(id) for id in article_ids if id.strip()]
        
        if not article_ids:
            messages.error(request, 'No articles selected.')
            return redirect('admin:moderation_articles')
        
        articles = Article.objects.filter(pk__in=article_ids, status='pending_review')
        rejected_count = 0
        
        for article in articles:
            article.status = 'rejected'
            article.save()
            rejected_count += 1
            
            # Create notification for author
            Notification.objects.create(
                recipient=article.author,
                sender=request.user,
                notification_type=Notification.Type.ARTICLE_REJECTED,
                message=f'Your article "{article.title}" has been rejected. Please review and resubmit.',
                content_object=article
            )
            notify_admins_of_moderator_action(request.user, 'rejected', article)
        
        # Update moderator stats
        if hasattr(request.user, 'moderator_profile'):
            moderator = request.user.moderator_profile
            moderator.articles_reviewed += rejected_count
            moderator.articles_rejected += rejected_count
            moderator.save()
        
        messages.success(request, f'{rejected_count} article{"s" if rejected_count != 1 else ""} rejected successfully.')
    
    return redirect('admin:moderation_articles')


@login_required
def moderator_bulk_delete_articles(request):
    """Bulk delete multiple articles."""
    if not (request.user.role in ['moderator', 'admin']):
        messages.error(request, 'You do not have permission to delete articles.')
        return redirect('dashboard')
    
    # Check moderator permissions
    if request.user.role == 'moderator' and hasattr(request.user, 'moderator_profile'):
        if not request.user.moderator_profile.can_delete_articles:
            messages.error(request, 'You do not have permission to delete articles.')
            return redirect('admin:moderation_articles')
    
    if request.method == 'POST':
        article_ids = request.POST.get('article_ids', '').split(',')
        article_ids = [int(id) for id in article_ids if id.strip()]
        
        if not article_ids:
            messages.error(request, 'No articles selected.')
            return redirect('admin:moderation_articles')
        
        articles = Article.objects.filter(pk__in=article_ids, status='pending_review')
        deleted_count = articles.count()
        articles.delete()
        
        messages.success(request, f'{deleted_count} article{"s" if deleted_count != 1 else ""} deleted successfully.')
    
    return redirect('admin:moderation_articles')
