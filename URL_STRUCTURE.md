# Blogora URL Structure Documentation

## Main URL Configuration

### Root URLs (`config/urls.py`)
- `/admin/` - Admin dashboard (admin namespace)
- `/` - Blog app (main content)
- `/collections/` - Collections system (core namespace)
- `/account/signup/` - Custom signup view
- `/accounts/` - Django allauth authentication
- `/users/` - User profiles and management
- `/comments/` - Comment system
- `/interactions/` - Like and save interactions
- `/notifications/` - Notification system (notifications namespace)
- `/recommendations/` - Recommendation engine (recommendations namespace)
- `/dashboard/` - User dashboard (dashboard namespace)
- `/api/v1/` - REST API (api namespace)
- `/api/schema/` - OpenAPI schema
- `/api/docs/` - Swagger documentation

## App-specific URL Structures

### Blog App (`apps/blog/urls.py`)
- `/` - Home page (blog:home)
- `/articles/` - Article list (blog:article_list)
- `/article/<slug>/` - Article detail (blog:detail)
- `/category/<slug>/` - Articles by category (blog:category)
- `/tag/<slug>/` - Articles by tag (blog:tag)
- `/create/` - Create article (blog:create)
- `/my-articles/` - User's articles (blog:my_articles)
- `/edit/<slug>/` - Edit article (blog:update)
- `/delete/<int:pk>/` - Delete article (blog:delete)

### Users App (`apps/users/urls.py`)
- `/profile/` - User profile (users:profile)
- `/profile/edit/` - Edit profile (users:edit_profile)
- `/profile/<str:username>/` - User profile view (users:user_profile)
- `/follow/<int:user_id>/` - Follow/unfollow user (users:follow_user)
- `/following/` - Following list (users:following)
- `/followers/` - Followers list (users:followers)
- `/signup/` - Custom signup (users:custom_signup)

### Core App (`apps/core/urls.py`)
- `/collections/` - Collection list (core:collection_list)
- `/collections/<int:pk>/` - Collection detail (core:collection_detail)
- `/collections/create/` - Create collection (core:collection_create)
- `/collections/<int:pk>/edit/` - Edit collection (core:collection_update)
- `/collections/<int:pk>/delete/` - Delete collection (core:collection_delete)
- `/collections/add/<int:article_id>/<int:collection_id>/` - Add to collection (core:add_to_collection)
- `/collections/article/<int:article_id>/` - Get collections for article (core:get_collections)
- `/saved/` - Saved articles (core:saved_articles)

### Comments App (`apps/comments/urls.py`)
- `/create/<int:article_id>/` - Create comment (comments:create_comment)
- `/edit/<int:comment_id>/` - Edit comment (comments:edit_comment)
- `/delete/<int:comment_id>/` - Delete comment (comments:delete_comment)
- `/thread/<int:comment_id>/` - Comment thread (comments:thread)

### Interactions App (`apps/interactions/urls.py`)
- `/like/article/<int:article_id>/` - Like article (interactions:like_article)
- `/like/comment/<int:comment_id>/` - Like comment (interactions:like_comment)
- `/save/article/<int:article_id>/` - Save article (interactions:save_article)
- `/likes/` - User's liked content (interactions:user_likes)

### Notifications App (`apps/notifications/urls.py`)
- `/` - Notification list (notifications:list)
- `/dropdown/` - Notification dropdown (notifications:dropdown)
- `/mark-read/<int:notification_id>/` - Mark as read (notifications:mark_read)
- `/mark-all-read/` - Mark all as read (notifications:mark_all_read)
- `/delete/<int:notification_id>/` - Delete notification (notifications:delete)
- `/preferences/` - Notification preferences (notifications:preferences)

### Recommendations App (`apps/recommendations/urls.py`)
- `/` - Recommendation dashboard (recommendations:dashboard)
- `/refresh/` - Refresh recommendations (recommendations:refresh)
- `/settings/` - Recommendation settings (recommendations:settings)
- `/similar/<int:article_id>/` - Similar articles (recommendations:similar)

### Admin App (`apps/admin/urls.py`)
- `/` - Admin dashboard (admin:dashboard)
- `/users/` - User management (admin:users)
- `/users/<int:pk>/` - User detail (admin:user_detail)
- `/articles/` - Article management (admin:articles)
- `/articles/<int:pk>/` - Article detail (admin:article_detail)
- `/articles/<int:pk>/approve/` - Approve article (admin:approve_article)
- `/articles/<int:pk>/reject/` - Reject article (admin:reject_article)
- `/users/<int:pk>/toggle-role/` - Toggle user role (admin:toggle_user_role)

## URL Structure Verification Status

✅ **Completed URLs:**
- Blog app URLs - All properly configured
- Users app URLs - All properly configured
- Core app URLs - All properly configured
- Comments app URLs - All properly configured
- Interactions app URLs - All properly configured
- Notifications app URLs - All properly configured
- Recommendations app URLs - All properly configured
- Admin app URLs - All properly configured

⚠️ **Needs Attention:**
- Dashboard app URLs - Empty, needs implementation

## URL Best Practices Followed

1. **Consistent Naming:** All URLs follow the pattern `app_name:view_name`
2. **RESTful Design:** URLs follow RESTful conventions
3. **SEO Friendly:** Slugs used for content URLs
4. **Security:** ID-based URLs for sensitive operations
5. **Namespacing:** All apps properly namespaced
6. **Versioning:** API URLs versioned (`/api/v1/`)

## Integration Points

- **HTMX Integration:** All interactive URLs support HTMX requests
- **API Endpoints:** RESTful API available at `/api/v1/`
- **Authentication:** Allauth integration at `/accounts/`
- **Admin:** Django admin and custom admin at `/admin/`

## Next Steps

1. Implement dashboard app URLs
2. Add URL testing
3. Document API endpoints
4. Add URL redirects for legacy support
