from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class AuthorRequiredMixin(LoginRequiredMixin):
    """
    Allows access only to users with role='author' or role='admin'.
    """
    def test_func(self):
        return self.request.user.role in ['author', 'admin']
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("You must be an author to access this page.")


class ModeratorRequiredMixin(LoginRequiredMixin):
    """
    Allows access only to users with role='moderator' or role='admin'.
    """
    def test_func(self):
        return self.request.user.role in ['moderator', 'admin']
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("You must be a moderator to access this page.")


class AdminRequiredMixin(LoginRequiredMixin):
    """
    Allows access only to users with role='admin' or is_staff=True.
    """
    def test_func(self):
        return self.request.user.role == 'admin' or self.request.user.is_staff
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("You must be an admin to access this page.")


class OwnerRequiredMixin(LoginRequiredMixin):
    """
    For object-based views: allows access only if request.user == obj.author (or obj.owner).
    """
    def test_func(self):
        obj = self.get_object()
        if obj is None:
            return False
        
        # Check if object has author attribute (Article) or owner attribute (Collection)
        if hasattr(obj, 'author'):
            return obj.author == self.request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == self.request.user
        
        return False
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("You can only access your own content.")
