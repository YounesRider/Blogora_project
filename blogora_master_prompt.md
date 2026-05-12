# BLOGORA — Complete Fix & Enhancement Master Prompt

> **How to use this prompt:** Paste it in its entirety to your AI coding assistant (Claude, Cursor, Copilot, etc.) along with your full Django project codebase. Work through the numbered sections one at a time, or ask the AI to tackle all of them sequentially. Every fix is grounded in the project's own Cahier de Charges and Rapport Technique.

---

## CONTEXT & IDENTITY

You are working on **Blogora**, a Django 5.x blog platform built with the MVT pattern. The project uses PostgreSQL, Django REST Framework, HTMX, Celery + Redis, django-allauth, and scikit-learn for recommendations. Your job is to fix, complete, and polish this application according to its Cahier de Charges and Rapport Technique. Always use only what Django and its ecosystem already provide — no React, no separate SPA. Bring your absolute best styling and UX work to every template change.

---

## SECTION 0 — GLOBAL RENAMES & BRANDING

**0.1 – Rename everything to "Blogora"**
- Search the entire project for any hardcoded site name (the old name, "My Blog", "Django Blog", or similar). Replace every occurrence with **Blogora**.
- In `settings.py`, set `SITE_NAME = "Blogora"` and use it in all templates via a context processor.
- Update `<title>` tags across all templates to follow the pattern: `{{ page_title }} — Blogora`.
- Update the `<meta name="description">` default to mention Blogora.
- Update the navbar brand logo/text to **Blogora** with a suitable icon (e.g., a feather or pen emoji rendered as SVG inline).
- Update the browser tab favicon (use an SVG data URI of a simple "B" monogram if no favicon exists).

---

## SECTION 1 — DATA MODELS (align with UML class diagram)

The canonical class diagram defines these entities and fields. Audit every model and make the following corrections:

**1.1 – User / Profile**
```
User: id, username, email, password, role (CharField with choices), date_joined
Profile (OneToOne → User): avatar, bio, social_links (JSONField), preferred_tags (ManyToMany → Tag), preferred_categories (ManyToMany → Category)
```
- `role` must have exactly **four** choices: `'guest'`, `'user'`, `'author'`, `'admin'`. Do not conflate this with Django's `is_staff`/`is_superuser` — keep them separate. An `admin` role user may or may not be `is_staff`.
- Add a `Follow` model: `follower (FK User)`, `following (FK User)`, `created_at`. Add a `unique_together` constraint so a user cannot follow the same person twice.
- Add helper properties to `Profile`: `followers_count`, `following_count`, `is_author` (returns `user.role == 'author'`).

**1.2 – Article**
```
Article: id, title, slug (auto from title, unique), content (TextField/RichTextField), cover_image (ImageField), status (choices: draft, pending_review, published, rejected, archived), created_at, updated_at, author (FK User), categories (M2M Category), tags (M2M Tag), view_count (PositiveIntegerField, default=0), auto_publish (BooleanField, default=False)
```
- `status` must include `pending_review` and `rejected` states for the admin approval workflow.
- `auto_publish`: if `True` for a given author (set by admin), the article skips the review queue and goes directly to `published`.
- On save, auto-generate `slug` from `title` if blank. Ensure uniqueness by appending `-2`, `-3`, etc.
- Add a `reading_time` property (estimate: `ceil(word_count / 200)` minutes).

**1.3 – Comment**
```
Comment: id, content (TextField), author (FK User), article (FK Article), parent (FK self, null=True, blank=True), is_approved (BooleanField, default=True), created_at
```
- Remove or set to 0 any minimum-length validator on `content`. A comment can be as short as 1 character.
- Keep `is_approved` for moderation but default it to `True` (auto-approved unless flagged).

**1.4 – Like (Generic)**
```
Like: id, user (FK User), content_type (FK ContentType), object_id (PositiveIntegerField), created_at
unique_together: (user, content_type, object_id)
```
- This is a single unified like model using Django's `GenericForeignKey`. A user can like an Article OR a Comment, but only once per object (enforced by `unique_together`).

**1.5 – Notification**
```
Notification: id, recipient (FK User), sender (FK User, null=True), notification_type (choices: comment, reply, like, follow, article_approved, article_rejected), message (TextField), is_read (BooleanField, default=False), content_type (FK ContentType, null=True), object_id (PositiveIntegerField, null=True), created_at
```

**1.6 – Collection** *(create if it does not exist)*
```
Collection: id, owner (FK User), name (CharField), description (TextField, blank=True), is_private (BooleanField, default=True), articles (M2M Article), created_at, updated_at
```
- Every new user automatically gets a private collection named **"Saved Posts"** (created via a `post_save` signal on `User`).
- Users can create additional public or private collections from their profile.
- Only the owner can see private collections; public collections are visible to everyone.

**1.7 – Run and verify migrations**
After all model changes, generate and apply migrations. Ensure no circular imports exist.

---

## SECTION 2 — PERMISSIONS & ROLE SYSTEM

**2.1 – Role definitions**

| Role | What they can do |
|------|-----------------|
| **Guest** (anonymous) | Read published articles, view public profiles and public collections |
| **User** (authenticated, role=`user`) | Everything a Guest can do + post comments, like/unlike articles and comments, save articles to their collections, follow/unfollow other users |
| **Author** (role=`author`) | Everything a User can do + create/edit/delete their own articles, access their author dashboard |
| **Admin** (role=`admin` or `is_staff=True`) | Everything an Author can do + approve/reject articles, grant/revoke author trust (auto_publish), manage users, moderate comments, access admin dashboard |

**2.2 – Custom mixins and decorators**

Create the following in `core/mixins.py`:
```python
class AuthorRequiredMixin(LoginRequiredMixin):
    """Allows access only to users with role='author' or role='admin'."""

class AdminRequiredMixin(LoginRequiredMixin):
    """Allows access only to users with role='admin' or is_staff=True."""

class OwnerRequiredMixin(LoginRequiredMixin):
    """For object-based views: allows access only if request.user == obj.author (or obj.owner)."""
```

**2.3 – Apply permissions in all views**
- `ArticleCreateView`, `ArticleUpdateView`, `ArticleDeleteView` → `AuthorRequiredMixin` + `OwnerRequiredMixin`.
- `AdminDashboardView`, article approval endpoints → `AdminRequiredMixin`.
- Comment post, like toggle, save-to-collection, follow → `LoginRequiredMixin`.
- Never show "Write Article", "Edit", "Delete" buttons to users without the right role — use template tags or `{% if request.user.profile.is_author %}`.

**2.4 – Registration role**
- New users receive `role='user'` by default on registration.
- Users can request to become an author via a simple form (sets a `requested_author` flag on their Profile). Admin approves this from the dashboard.

---

## SECTION 3 — AUTHENTICATION & SIGN-UP FLOW

**3.1 – Complete the sign-up UI**
The sign-up page must be a beautiful, multi-step (or single-page with sections) form that collects:
1. **Step 1:** Username, email, password, confirm password.
2. **Step 2 (Interests):** A visually appealing grid of category cards and tag chips. The user selects up to 5 categories or tags they are interested in. These are saved to `Profile.preferred_categories` and `Profile.preferred_tags`. This step feeds the recommendation cold-start.

Style the interests selector as clickable cards with icons/colors. Selected cards should get a highlighted border. Use JavaScript (vanilla or HTMX) to enforce the max-5 limit client-side and show a count badge ("3/5 selected").

**3.2 – Fix the login page UI**
- Center the login card on the page with a clean two-column layout (left: branding/hero text, right: form) on desktop; single column on mobile.
- Show password toggle (eye icon, pure JS).
- Add "Remember me" checkbox.
- Add a link: "Don't have an account? Join Blogora".

**3.3 – Email confirmation**
- After registration, redirect to a "Check your email" confirmation page, not back to login immediately.
- Ensure the confirmation email template is branded as Blogora.

---

## SECTION 4 — ARTICLE EDITOR (Author Publication Page)

This is a complete redesign of the article creation/editing interface.

**4.1 – Rich text editor**
- Integrate **django-ckeditor 5** (or **Quill.js** if CKEditor is already present) for the `content` field.
- The editor must support: headings (H1–H4), bold, italic, underline, strikethrough, blockquote, code block, ordered/unordered lists, links, image upload (inline), horizontal rule, text alignment, undo/redo.
- The editor toolbar must be visible and not hidden behind a scroll. Use a sticky toolbar.

**4.2 – Article form layout**
Redesign `blog/templates/blog/article_form.html` as a two-panel layout:
- **Left panel (70%):** Title input (large, prominent, placeholder "Your article title…"), subtitle/excerpt input, the rich text editor body.
- **Right panel (30%, sticky):** Cover image upload with drag-and-drop preview, category multi-select (checkboxes with colored labels), tag input (tokenized chip input — a user types and presses Enter/comma to add a tag), status selector (Draft / Submit for Review), and the **Publish / Save Draft** button.

**4.3 – Fix the Publish button**
The publish action must:
1. Validate the form server-side.
2. If the author has `auto_publish=True` on their Profile → set `article.status = 'published'` immediately and redirect to the article detail page with a success message.
3. Otherwise → set `article.status = 'pending_review'`, save, redirect to the author dashboard with message: "Your article has been submitted for review."
4. A "Save as Draft" button must always be available and save with `status='draft'` without submitting for review.
5. Show clear Django messages (success/error/info) after every action.

**4.4 – Article preview**
Add a "Preview" button (opens the article in a new tab/modal with a `?preview=true` query param that bypasses the published-only filter for the article's own author).

**4.5 – Author dashboard overhaul**
`dashboard/templates/dashboard/author_dashboard.html` must display:
- **Stats cards** (row): Total articles, Total views, Total likes received, Total comments received — each in a styled card with an icon and trend indicator.
- **Articles table:** Title | Status (colored badge) | Views | Likes | Comments | Created | Actions (Edit / Delete / Preview). Sortable columns. Filterable by status.
- **Status badges:** `draft` → grey, `pending_review` → amber, `published` → green, `rejected` → red, `archived` → blue-grey.
- **Rejection reason:** If an article was rejected, show the admin's rejection note inline in the table row, expandable.
- **Quick actions:** "New Article" button always visible at the top.

---

## SECTION 5 — ADMIN DASHBOARD

**5.1 – Article moderation queue**
`dashboard/templates/dashboard/admin_dashboard.html` must have a dedicated "Pending Review" tab/section showing all articles with `status='pending_review'`:
- Article title, author name, submitted date, estimated reading time.
- "Approve" button → sets `status='published'`, sends notification to author.
- "Reject" button → opens a small inline form asking for a rejection reason (TextField), sets `status='rejected'`, sends notification to author with the reason.
- "Approve & Trust Author" button → sets `status='published'` AND sets `author.profile.auto_publish = True`, sends notification: "Congratulations! Your articles will now be published automatically."

**5.2 – Author trust management**
A table of all authors showing their `auto_publish` status with a toggle switch. Admin can revoke trust (set `auto_publish=False`) at any time.

**5.3 – User management**
- List of all users with their role, join date, article count.
- Ability to change a user's role (promote to author, demote, etc.).
- Ability to approve "author requests" (users who have requested the author role).

**5.4 – Comment moderation**
- List of flagged/reported comments with approve/delete actions.

---

## SECTION 6 — BLOG INTERACTIONS (Facebook-style reactions)

**6.1 – Single interaction type per object (toggle)**
A user may only place **one** interaction on any given article or comment at a time. The interaction is a toggle: clicking the active reaction removes it (unlike). This is enforced at the database level by the `unique_together` on `Like`.

**6.2 – Like button (HTMX)**
Replace any broken like implementation with a clean HTMX-powered toggle:

```html
<!-- In article_detail.html -->
<button
  hx-post="{% url 'likes:toggle' content_type_id=article_ct_id object_id=article.pk %}"
  hx-target="#like-section-{{ article.pk }}"
  hx-swap="outerHTML"
  hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'
  class="like-btn {% if user_has_liked %}liked{% endif %}"
>
  <span class="like-icon">👍</span>
  <span class="like-count">{{ like_count }}</span>
</button>
```

The view at `likes:toggle` must:
1. Require authentication (return a 401 / redirect to login if anonymous).
2. Use `get_or_create` + delete pattern: if like exists, delete it (unlike); if not, create it.
3. Return only the `#like-section` partial HTML (not a full page) for HTMX to swap.
4. Return the updated count and the new `liked` state.

Apply the same pattern to comments.

**6.3 – Comment interactions**
- Each comment also has a like button (same HTMX pattern, `content_type` points to Comment).
- Reply button expands an inline reply form (HTMX `hx-get` loading the reply form into a target div below the comment).

---

## SECTION 7 — COMMENTS

**7.1 – Remove the minimum character validator**
Find any `MinLengthValidator` or `min_length` on `Comment.content` and remove it entirely. There is no minimum length for comments.

**7.2 – Comment form UX**
- The comment textarea should auto-expand as the user types.
- Pressing Shift+Enter inserts a newline; Enter alone does NOT submit (to avoid accidental submissions on desktop).
- A submit button labeled "Post Comment" is always visible.
- After posting, the new comment appears at the top of the list via HTMX without a full page reload.

**7.3 – Nested replies (one level)**
- Each top-level comment has a "Reply" link. Clicking it reveals an inline reply form.
- Replies are displayed indented under their parent comment.
- Maximum nesting depth: 1 (replies cannot have replies).

---

## SECTION 8 — COLLECTIONS (Saved Posts)

**8.1 – Default private collection**
Via a `post_save` signal on `User` (or `Profile`), automatically create a Collection named "Saved Posts" (`is_private=True`) for every new user.

**8.2 – Save to Collection UI**
On every article card and article detail page, add a "Save" / bookmark icon button. Clicking it:
- If the user has only the default collection → adds to "Saved Posts" immediately and shows a toast notification.
- If the user has multiple collections → opens a small dropdown/modal listing their collections (with a checkbox next to each). The user selects one or more collections to save to, then confirms.
- The button state changes to "Saved" (filled bookmark icon) if the article is already in at least one of the user's collections.

**8.3 – Collections page**
`/profile/<username>/collections/` shows all **public** collections of that user. The owner also sees their private collections here (with a 🔒 lock icon).

Each collection page (`/collections/<id>/`) lists its articles in a grid, shows the collection name, description, visibility, and article count. Only the owner can edit or delete a collection.

**8.4 – Create/Edit Collection form**
Simple form: Name, Description, Public/Private toggle. Available from the user's profile page.

---

## SECTION 9 — FOLLOW SYSTEM

**9.1 – Follow / Unfollow**
- Add a "Follow" button on every user profile page.
- Clicking follow creates a `Follow(follower=request.user, following=profile_user)` record.
- Clicking again (unfollow) deletes the record.
- Use HTMX for the toggle (no page reload).
- The button shows "Following ✓" when the current user already follows this person, and "Follow" otherwise.
- **No DM/messaging feature.** Only the follow relationship.

**9.2 – Follower/Following counts**
Display follower and following counts on every profile page.

**9.3 – Follow notifications**
When user A follows user B, create a Notification for user B: `notification_type='follow'`, message "{{ follower.username }} started following you."

**9.4 – Feed (optional but ideal)**
On the home page, if the user is logged in, add a "Following" feed tab that shows recent articles from authors the user follows, sorted by `created_at` descending.

---

## SECTION 10 — RECOMMENDATION SYSTEM (audit & fix)

Audit the current `recommendations/` app against these specifications:

**10.1 – Model alignment check**
The recommendation engine must NOT have a `Recommendation` database table. It must work entirely from the existing `Like`, `Comment`, `Article`, `Tag`, `Category`, and `Profile.preferred_tags/preferred_categories` data. If a `Recommendation` table exists, remove it and rewrite the logic.

**10.2 – Cold start**
- New users with no interaction history → show articles from their `Profile.preferred_categories` and `Profile.preferred_tags` (set during sign-up). If no preferences either → show trending (most liked in the last 7 days).
- Transition to personalized feed once the user has ≥ 5 likes or comments.

**10.3 – Algorithm**
- Collaborative filtering via KNN: build a user × article interaction matrix from `Like` and `Comment` records. Find K=10 nearest users by cosine similarity. Recommend articles those users liked that the current user hasn't interacted with yet.
- Content-based via TF-IDF: vectorize article title+tags+categories. Recommend articles cosine-similar to ones the user has liked.
- Blend both signals (e.g., 60% collaborative, 40% content-based).
- Cache results in Redis per `user_id` with TTL=30 minutes.

**10.4 – Feed placement**
- On the home page, the "Recommended for You" section (already in the spec) must call the recommendation API endpoint and render results. If Redis is unavailable or cache is cold, fall back to trending articles.
- The section must be clearly labeled "Recommended for You" and only shown to logged-in users.

**10.5 – Negative sampling (Celery task)**
Keep the existing negative sampling Celery task if it exists and is correct. If it is broken or missing, implement it: for each user with ≥ 5 interactions, generate a training dataset with positive examples (liked/commented articles) and k=5 random negative examples (articles in the same categories not interacted with).

---

## SECTION 11 — NOTIFICATIONS

**11.1 – Bell icon in navbar**
- Show an unread count badge on the bell icon.
- Use HTMX polling (`hx-trigger="every 30s"`) or Django Channels to update the count.
- Clicking the bell opens a dropdown showing the latest 10 notifications with mark-as-read.

**11.2 – Notification triggers (ensure all exist)**
- New comment on author's article → notify author.
- Reply to a comment → notify the parent commenter.
- Like on article/comment → notify the content owner.
- New follower → notify the followed user.
- Article approved → notify the submitting author.
- Article rejected (with reason) → notify the submitting author.

**11.3 – Mark all as read**
A "Mark all as read" button in the notifications dropdown/page.

---

## SECTION 12 — UI/UX — GLOBAL STYLING

Apply a cohesive, premium visual design across all templates. You are working exclusively with Django templates, vanilla CSS/JS, and HTMX — no React, no Tailwind CDN JIT. Use Bootstrap 5 (CDN) as the foundation, supplemented by a custom `static/css/blogora.css` override file.

**12.1 – Design tokens (add to `blogora.css`)**
```css
:root {
  --brand-primary: #2563eb;       /* Blogora blue */
  --brand-primary-dark: #1d4ed8;
  --brand-accent: #f59e0b;        /* Amber accent */
  --surface: #ffffff;
  --surface-alt: #f8fafc;
  --border: #e2e8f0;
  --text-primary: #0f172a;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 20px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
  --shadow-lg: 0 8px 32px rgba(0,0,0,0.12);
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-serif: 'Playfair Display', Georgia, serif;
}
```

Import Inter and Playfair Display from Google Fonts in `base.html`.

**12.2 – Navbar**
- Full-width, white background, subtle bottom border.
- Left: Blogora logo (feather icon SVG + bold "Blogora" wordmark).
- Center (desktop): main nav links (Home, Explore, Categories).
- Right: Search bar (collapsible on mobile), notification bell (authenticated), user avatar dropdown (authenticated) or "Log in / Sign up" buttons (anonymous).
- Sticky at top with a subtle box-shadow on scroll (JS scroll listener adds a class).
- Mobile: hamburger menu with smooth slide-in sidebar.

**12.3 – Article cards**
- Clean card with rounded corners, subtle shadow on hover, cover image (16:9, object-fit cover), category badge (colored pill), title (serif font, 2-line clamp), excerpt (2-line clamp, muted), author avatar + name + date, reading time, like count. 
- On hover: the card lifts slightly (`transform: translateY(-3px)`, shadow deepens) with a CSS transition.

**12.4 – Article detail page**
- Full-width cover image (max-height 480px, object-fit cover) at the top.
- Article content in a centered, max-width 720px column with generous line-height (1.8) and serif body font.
- Author card sidebar (on desktop, sticky) showing avatar, name, bio, follow button, follower count.
- Interaction bar (like button, save button, share buttons) sticky at the bottom on mobile, in a floating pill on desktop.

**12.5 – Profile page**
- Hero section: cover image (or gradient), large avatar, display name, username, bio, social links, follower/following counts, follow button.
- Tabs: Articles | Collections | About.
- Articles tab: masonry or 3-column grid of article cards.

**12.6 – Forms (login, signup, article editor)**
- All form inputs: rounded, with focus ring in brand primary color, floating labels (CSS-only).
- Error states: red border + red error message below the field.
- Success state: brief green checkmark animation on submit.

**12.7 – Toast notifications**
Convert all Django `messages` to floating toast notifications (bottom-right, 4s auto-dismiss, with close button). Use CSS animations for slide-in/slide-out.

**12.8 – Empty states**
Every list that could be empty (no articles, no notifications, no followers) must have a friendly illustrated empty-state: icon + heading + subtext + CTA button.

**12.9 – Loading states**
All HTMX requests must show a loading spinner inside the target element while the request is in flight (`hx-indicator` pattern).

---

## SECTION 13 — PERFORMANCE & SECURITY FIXES

**13.1 – N+1 queries**
Audit all list views. Use `select_related` and `prefetch_related` wherever relationships are traversed in templates. At minimum:
- Article list: `prefetch_related('tags', 'categories', 'likes')`, `select_related('author', 'author__profile')`.
- Comment list: `select_related('author', 'author__profile', 'parent')`.

**13.2 – CSRF**
Ensure all HTMX POST/PUT/DELETE requests include the CSRF token. Use the `hx-headers` meta tag pattern in `base.html`:
```html
<meta name="htmx-config" content='{"defaultSwapStyle":"outerHTML", "includeIndicatorStyles":false}'>
```
And add a global HTMX `htmx:configRequest` handler in JS to inject the CSRF header.

**13.3 – Permission checks in views**
Every view that modifies data must check permissions server-side (not just in templates). Return `403 Forbidden` or redirect to login appropriately.

**13.4 – Media files**
Ensure `MEDIA_URL` and `MEDIA_ROOT` are configured. Profile avatars and article cover images must be saved under `media/avatars/` and `media/articles/covers/` respectively. Use `Pillow` to resize images on upload (max 1920px wide for covers, max 400px for avatars).

---

## SECTION 14 — URL STRUCTURE

Ensure all these URL patterns exist and work:

```
/                               → home (article list, recommendations)
/articles/<slug>/               → article detail
/articles/create/               → article create (author only)
/articles/<slug>/edit/          → article edit (owner only)
/articles/<slug>/delete/        → article delete (owner only)
/articles/<slug>/preview/       → article preview (owner only)
/profile/<username>/            → user profile
/profile/<username>/follow/     → follow/unfollow toggle (HTMX POST)
/profile/<username>/collections/→ user collections list
/collections/<int:pk>/          → collection detail
/collections/create/            → create collection
/collections/<int:pk>/edit/     → edit collection
/dashboard/                     → author dashboard (author+)
/dashboard/admin/               → admin dashboard (admin only)
/dashboard/admin/articles/      → pending articles queue
/dashboard/admin/users/         → user management
/notifications/                 → notification list
/notifications/mark-read/       → mark all as read
/likes/toggle/                  → like toggle endpoint (HTMX)
/comments/<int:pk>/reply/       → reply form partial (HTMX GET)
/search/                        → search results
/accounts/login/                → login
/accounts/signup/               → sign up (step 1)
/accounts/signup/interests/     → sign up interests (step 2)
```

---

## SECTION 15 — TESTING CHECKLIST

After implementing all of the above, manually verify:

- [ ] A new user can sign up, pick interests, and land on the home page with relevant articles.
- [ ] Login and logout work. Password reset sends an email.
- [ ] An author can create a draft article, see it in their dashboard.
- [ ] Publishing submits for review (pending_review status) unless auto_publish is enabled.
- [ ] Admin can see pending articles, approve them, and the article goes live.
- [ ] Admin can reject with a reason; author sees the reason in their dashboard.
- [ ] Admin can trust an author (auto_publish=True); subsequent articles publish instantly.
- [ ] A user can like an article (count increments). Liking again unlikes. Cannot like twice.
- [ ] A user can like a comment. Same toggle logic.
- [ ] A user can comment. Comment of any length (even "ok") posts successfully.
- [ ] A user can reply to a comment (one level deep).
- [ ] A user can save an article to their collections.
- [ ] Default "Saved Posts" collection exists for every user.
- [ ] Private collections are only visible to owner.
- [ ] A user can follow another user. Follower count updates.
- [ ] Notifications appear for all trigger events.
- [ ] The recommendation section on the home page shows relevant articles (not an error).
- [ ] All pages are mobile-responsive.
- [ ] All forms show proper validation errors.
- [ ] No 500 errors on any page.
- [ ] Site name reads "Blogora" everywhere.

---

## APPENDIX — KEY MODELS SUMMARY (from UML)

```
User          ──OneToOne──▶  Profile
User          ──FK(author)──▶ Article (many)
User          ──FK(recipient)▶ Notification (many)
User          ──FK(follower)──▶ Follow
User          ──FK(following)──▶ Follow
Article       ──M2M──▶ Category
Article       ──M2M──▶ Tag
Article       ──FK(article)──▶ Comment (many)
Comment       ──FK(self)──▶ Comment (parent, nullable)
Like          ──GFK──▶ Article OR Comment
Collection    ──FK(owner)──▶ User
Collection    ──M2M──▶ Article
```

No `Recommendation` table exists — the recommendation engine is purely computed from the above.

---

*End of Blogora Master Prompt — v1.0*
