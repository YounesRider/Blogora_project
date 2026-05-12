# Blogora Project Architecture

## Overview
Blogora is a Django-based content publishing platform with personalized recommendations, social interactions, article tracking, and taxonomy management.

This document summarizes the project structure and behaviour for generating UML diagrams including:
- Use case diagrams
- Sequence diagrams
- Class diagrams
- Package diagrams
- Activity diagrams
- Communication diagrams
- State diagrams

## High-level Architecture

The application follows a modular Django architecture composed of reusable apps:
- `apps.blog`: core article publishing and browsing
- `apps.users`: user profiles, authentication, and roles
- `apps.comments`: article comments and moderation
- `apps.interactions`: likes, saves, reactions, and article view tracking
- `apps.recommendations`: recommendation engine, prediction, and training
- `apps.notifications`: notifications for users
- `apps.taxonomy`: categories, tags, and article classification
- `apps.api`: REST endpoints for AJAX and external features
- `apps.core`: shared models, mixins, utilities, and site-level views
- `config`: project configuration, URL routing, and environment settings

## Package Diagram Description

Each Django app acts as a package. Relationships are:
- `apps.blog` depends on `apps.users`, `apps.taxonomy`, `apps.interactions`, and `apps.recommendations`.
- `apps.recommendations` depends on `apps.blog` and `apps.interactions`.
- `apps.api` depends on `apps.blog`, `apps.recommendations`, `apps.taxonomy`, and `apps.interactions`.
- `apps.comments` depends on `apps.blog` and `apps.users`.
- `apps.notifications` depends on `apps.users` and application events.
- `apps.core` contains shared base models and mixins used by all apps.
- `config` ties apps together through URL routing and settings.

## Core Domain Classes

### `apps.blog.models.Article`
Properties:
- `id`, `title`, `slug`, `content`, `cover_image`, `status`, `auto_publish`, `view_count`
- `author` (FK to `users.User`)
- `categories` (M2M to `taxonomy.Category`)
- `tags` (M2M to `taxonomy.Tag`)
- `likes` generic relation to `interactions.Like`

Computed properties:
- `reading_time`: calculates an estimate using a 200 words-per-minute rule and strips HTML content.
- `likes_count`, `saves_count`, `reaction_counts`, `reaction_types`

### `apps.users.models.User`
User accounts and profile data.

### `apps.comments.models.Comment`
Comments linked to `Article` and `User`.

### `apps.interactions.models.Like`
Generic like entity attached to articles and possible other content.

### `apps.interactions.models.SavedArticle`
Bookmark relationship between `User` and `Article`.

### `apps.interactions.models.Reaction`
Emojis and reaction types on articles.

### `apps.interactions.models.ArticleView`
Tracks when a user views an article and stores `reading_duration` in seconds.

### `apps.taxonomy.models.Category` and `Tag`
Used for filtering and organizing articles.

## Use Case Summary

### Primary Use Cases
- `Browse Articles`
- `View Article`
- `Estimate Reading Time`
- `Track Reading Duration`
- `Like Article`
- `Save Article`
- `React to Article`
- `Comment on Article`
- `Publish Article`
- `Recommend Articles`
- `Search by Category/Tag`
- `Manage Profile`
- `Admin Review Articles`

### Use Case Actors
- `Guest`
- `Registered User`
- `Author`
- `Administrator`
- `Recommendation Engine`

## Sequence Diagram Flows

### 1. Article List View
1. Browser requests `GET /articles/`.
2. `apps.blog.views.ArticleListView` builds queryset and fetches published articles.
3. Query uses `select_related('author')`, `prefetch_related('categories', 'tags')`, and annotations for like/save counts.
4. View renders `templates/blog/article_list.html` and sends full response.
5. Browser displays article cards with `{{ article.reading_time }}` values.

### 2. Article Detail View
1. Browser requests `GET /article/<slug>/`.
2. `apps.blog.views.ArticleDetailView` loads article, increments `view_count`, and creates `ArticleView` if user authenticated.
3. Context includes interaction state and similar articles.
4. Template `templates/blog/article_detail.html` renders the article and includes `data-article-id` for JS tracking.
5. Client JS calculates elapsed reading time and sends `POST /api/v1/track-reading/<article_id>/` when the page unloads.
6. `apps.api.views.track_reading` updates or creates `ArticleView.reading_duration`.

### 3. Reading Time Tracking
1. `static/js/main.js` initializes on DOM load.
2. `trackReadingTime()` locates the article element and starts a timer.
3. When user leaves the page, the script posts duration using `fetch(..., keepalive: true)`.
4. The backend receives the duration and preserves the maximum reading duration per user-article pair.

### 4. Recommendation Request
1. Browser or server requests recommendations for a user.
2. `apps.recommendations.predict.get_recommendations()` returns article IDs.
3. The view loads matching `Article` objects, prefetched with `author` and `categories`.
4. Recommended article cards display on pages like the home and article list.

## Activity Diagram Notes

### Article Publishing Activity
- Author opens `article_create` form.
- Form validates and assigns author.
- If `pending_review` and auto-publish enabled, status becomes `published`.
- Article saves with generated slug.
- User sees `My Articles` or publication confirmation.

### Article Reading Activity
- User opens article detail.
- Page displays reading estimate and content.
- JS tracks reading duration.
- On page exit, duration is sent to backend.
- Backend saves `ArticleView.reading_duration`.
- Recommendation engine can later use this reading signal.

### Recommendation Refresh Activity
- Recommendation engine loads user history.
- Feature weights combine views, reading duration, likes, and other signals.
- It returns an ordered set of article IDs.
- The app displays those IDs as recommended articles.

## Communication Diagram Description

### Browser ↔ Server
- GET requests for pages and assets.
- POST requests for interaction APIs.
- AJAX-based tracking and likes use REST endpoints under `/api/v1/`.
- CSRF tokens are included for authenticated POST calls.

### Server ↔ Database
- ORM queries to fetch `Article`, `User`, `ArticleView`, `Like`, `SavedArticle`, and taxonomy models.
- Annotated queries and prefetches are used to reduce N+1 problems.
- `Article.save()` guarantees slug uniqueness and enforces content consistency.

### Recommendation Engine
- `apps.recommendations.predict` returns personalized IDs.
- `apps.recommendations.feature_engineering` computes signals like `reading_bonus` from `ArticleView.reading_duration`.

## State Diagram Candidates

### Article Lifecycle States
- `draft`
- `pending_review`
- `published`
- `rejected`
- `archived`

Transitions:
- `draft` -> `pending_review`
- `pending_review` -> `published` or `rejected`
- `published` -> `archived`

### User Interaction State
- `authenticated` / `unauthenticated`
- `liked` / `not liked`
- `saved` / `not saved`
- `view recorded` / `view not recorded`

### Reading Tracking State
- `not started`
- `reading`
- `sent`
- `completed`

## Implementation Notes

- `config/urls.py` routes major app namespaces.
- `apps/api/urls.py` exposes tracking and onboarding endpoints.
- `templates/blog/article_list.html`, `templates/blog/home.html`, and `templates/recommendations/dashboard.html` all display reading estimates.
- `apps.bl` model property `reading_time` computes estimates dynamically and now handles empty or HTML-rich content.
- `static/js/main.js` is responsible for client-side tracking and client interactivity.

## Diagramming Tips

- For class diagrams, show `Article` at the center with relationships to `User`, `Category`, `Tag`, `Like`, `SavedArticle`, and `ArticleView`.
- For package diagrams, group apps by feature area: content, user/interactions, recommendations, API, and infrastructure.
- For sequence diagrams, use cases like `Browse Article`, `Track Reading Time`, and `Generate Recommendations`.
- For activity diagrams, map the author publishing workflow and the reader consumption/tracking workflow.
- For state diagrams, model the article publication lifecycle and the reading tracker state machine.

## Files of Interest
- `apps/blog/models.py`
- `apps/blog/views.py`
- `apps/blog/urls.py`
- `apps/api/views.py`
- `apps/api/urls.py`
- `apps/interactions/models.py`
- `static/js/main.js`
- `templates/blog/article_detail.html`
- `templates/blog/article_list.html`
- `templates/blog/home.html`
- `apps/recommendations/predict.py`
- `apps/recommendations/feature_engineering.py`
- `config/urls.py`
