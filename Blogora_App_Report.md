# Blogora Application Report

## 1. Project Overview

Blogora is a Django-based blogging platform built around a modern content experience with social interactions, nested comments, and personalized article recommendations. The project combines standard CMS features with a recommendation engine powered by implicit interaction signals and category preferences.

### Key capabilities
- Article publishing and moderation
- Nested comments with replies and moderation support
- Like/save interactions for articles
- User profiles with preferences and notification settings
- Personalized recommendation system
- Read-time tracking and intelligent article scoring
- REST API endpoints for interaction and recommendation access

## 2. Core Application Structure

The project uses a modular Django architecture. Applications are separated by domain responsibility:

- `apps.blog`: article creation, editing, browsing, and detail views
- `apps.users`: user accounts, roles, profiles, and preferences
- `apps.comments`: comment storage, nesting, moderation, and display
- `apps.interactions`: likes, saves, article views, and user engagement signals
- `apps.recommendations`: recommendation model training, prediction, and UI
- `apps.notifications`: notification creation, dropdown rendering, and preferences
- `apps.taxonomy`: categories and tags for articles
- `apps.api`: REST endpoints, including recommendation delivery and reading tracking
- `apps.core`: shared models, mixins, and reusable utilities
- `config`: project URLs and settings

## 3. Data Model Summary

### `apps.blog.models.Article`

The `Article` model is the central content unit. Key fields:
- `author`: relationship to `users.User`
- `title`, `slug`, `content`, `cover_image`
- `status`: draft, published, pending_review, etc.
- `view_count`
- `categories`, `tags`

Computed fields and utilities include:
- `reading_time`: calculated from text length and average reading speed
- metadata shortcuts such as likes, saves, and comment counts

### `apps.users.models.User` and `UserProfile`

Users are extended with profile information and recommendation preferences:
- `preferred_categories`
- `preferred_tags`
- notification toggles for comments, likes, saves, replies

### Interaction models

- `apps.interactions.models.Like`: generic likes attached to articles and other content
- `apps.interactions.models.SavedArticle`: saved/bookmarked articles
- `apps.interactions.models.ArticleView`: tracks user article views and reading duration
- `apps.interactions.models.Reaction`: emoji-style reactions on content

### Recommendation models

- `apps.recommendations.models.RecommendationScore`
  - stores precomputed scores for `(user, article)` pairs
  - used by the dashboard and some UI flows to avoid recomputing every request

## 4. Recommendation System Architecture

The recommendation engine is implemented in two layers:

1. **Precomputed scored recommendations** through `RecommendationScore`
2. **On-the-fly ML/cold-start predictions** through an SVD-based model and fallback heuristics

### 4.1 Recommendation file map

- `apps/recommendations/predict.py`
- `apps/recommendations/feature_engineering.py`
- `apps/recommendations/train_model.py`
- `apps/recommendations/models.py`
- `apps/recommendations/views.py`
- `apps/recommendations/management/commands/generate_recommendations.py`

### 4.2 Recommendation scoring pipeline

#### Feature engineering

The recommendation engine uses implicit interaction signals to build a user×article score matrix in `apps/recommendations/feature_engineering.py`.

Weights in the scoring matrix:
- `Like` → 3.0
- `SavedArticle` → 2.0
- `ArticleView` → 1.0 + `reading_duration/60 * 0.5`

The pipeline aggregates these interactions by `(user_id, article_id)` and then adds a small number of negative samples for unseen user/article pairs.

#### Article features

The recommendation system also computes article-level metadata:
- freshness score via exponential decay over 30 days
- popularity score as `likes * 3 + saves * 2 + view_count * 0.1`
- comment count
- category count and tag count
- estimated read time

This feature set is available to the prediction layer when scoring or applying bonuses.

### 4.3 Model training

Training is handled by `apps/recommendations/train_model.py`.

Key steps:
- build the interaction matrix from `build_user_article_matrix()`
- encode user IDs and article IDs to integer indices
- create a sparse matrix from weighted interactions
- train `sklearn.decomposition.TruncatedSVD`
- normalize user and article factor vectors
- save the model to `apps/recommendations/model/recommender.pkl`

A warning is emitted if there are less than `MIN_INTERACTIONS = 10` positive training interactions.

### 4.4 Runtime prediction

`apps/recommendations/predict.py` is the runtime prediction module.

Main logic in `get_recommendations(user_id, top_k=10, exclude_seen=True)`:
- if the user has no interactions, treat them as a new user
- load the saved SVD model from `recommender.pkl`
- if the user is not part of the model or model file is missing, fallback to preference-based recommendations
- if the user exists in the model:
  - compute similarity scores as `article_factors @ user_vec`
  - add a comment engagement bonus: `comment_count * 0.1`
  - exclude seen articles from views, likes, and saves
  - return top K article IDs

### 4.5 Cold-start and fallback logic

For new users or users not in the model, `_recommendations_for_new_user()` is used.

It depends on the user's `UserProfile.preferred_categories`:
- returns published articles in preferred categories
- orders by `view_count`, `comment_count`, `created_at`
- excludes already seen content if `exclude_seen=True`
- if no preferences exist, falls back to a popularity function `_fallback_popular()`

The popularity fallback orders published articles by:
- `view_count`
- `comment_count`
- `created_at`

### 4.6 Precomputed recommendation scores

`apps/recommendations/views.py` implements another retrieval path based on `RecommendationScore`.

Flow in `get_recommendations(user_id, top_k=10, exclude_seen=True)`:
- loads `RecommendationScore` rows for the user
- filters out articles the user already interacted with
- if scores exist, returns ranked article IDs
- if no precomputed scores exist, invokes the predictive cold-start function from `apps.recommendations.predict`

This means the system can serve:
- `RecommendationScore` results for cached or batch-computed lists
- live fallback recommendations if precomputed scores are missing

### 4.7 Recommendation management and dashboard

Endpoints and UI in `apps/recommendations`:
- `recommendation_dashboard` → `/recommendations/`
- `refresh_recommendations` → `/recommendations/refresh/`
- `recommendation_settings` → `/recommendations/settings/`
- `get_article_recommendations` → `/recommendations/similar/<article_id>/`

`recommendation_dashboard()` builds context for the logged-in user:
- recommended articles
- recent likes
- trending articles
- like/save state for page articles
- pagination support

`refresh_recommendations()` can force regeneration of recommendations using the management helper exposed in `generate_recommendations.py`.

### 4.8 Batch generation of recommendations

`apps/recommendations/management/commands/generate_recommendations.py` contains CLI logic to regenerate recommendation scores for all users.

Behavior:
- deletes old `RecommendationScore` records
- iterates users in batches
- calls `get_recommendations(user_id, top_k, exclude_seen=True)`
- writes new `RecommendationScore` rows with rank-based scores

This command is intended for periodic batch updates, and the view can call it for manual refresh.

### 4.9 Recommendation integration points

The recommendation engine is integrated in several places:

- `apps.blog.views.home()`: adds `recommended_articles` to the home page for authenticated users
- `apps.api.views.my_recommendations()`: returns recommended articles via API
- `apps.notifications.views.notification_dropdown()`: populates a notification dropdown with 3 recommended articles
- `apps.recommendations.views.recommendation_dashboard()`: user-facing recommendation dashboard

## 5. Related User Behavior and Engagement Tracking

### Read-time tracking

JavaScript in `static/js/main.js` tracks reading duration:
- attaches to article pages with `article[data-article-id]`
- measures time from page load until pagehide/beforeunload/visibility hidden
- only sends durations longer than 10 seconds
- posts to `/api/v1/track-reading/<article_id>/`

Backend storage in `apps.api.views.track_reading()`:
- updates or creates `ArticleView`
- stores maximum reading duration for repeated visits
- returns success payload with duration

### Interaction signals

Interactions that feed recommendations include:
- `ArticleView`
- `Like`
- `SavedArticle`
- `Comment`

The feature engineering layer uses these signals with explicit weights, so article engagement strongly influences recommendations.

## 6. Notification and Recommendation Coupling

`apps.notifications.views.notification_dropdown()` builds the notification dropdown and also fetches recommended articles for the logged-in user.

This means notifications are enriched with recommendations and the recommendation engine is used in both content discovery and the notification UI.

## 7. API Endpoints

### Recommendation API
- `GET /api/recommendations/` → returns user-specific recommended articles via `apps.api.views.my_recommendations`
- `GET /api/v1/onboarding_categories/` → returns category list used during onboarding

### Reading tracking API
- `POST /api/v1/track-reading/<article_id>/` → records reading duration

### Recommendation dashboard route
- `GET /recommendations/`
- `POST /recommendations/refresh/`
- `GET /recommendations/settings/`
- `GET /recommendations/similar/<article_id>/`

## 8. Report of All Main App Features

### `apps.blog`
- article list, article detail, author dashboard
- category/tag filtering and search
- article creation and editing forms
- reading time estimation
- article detail metrics and similar content suggestions

### `apps.users`
- custom `User` model with role support
- `UserProfile` and notification preferences
- user registration, login, and profile management
- `preferred_categories` and `preferred_tags` for cold-start recommendations

### `apps.comments`
- nested comments with parent relations
- moderation controls
- reply handling and comment badges
- comment notification integration

### `apps.interactions`
- likes on articles and comments
- saved articles/bookmarks
- article views and reading duration tracking
- reaction types and counts

### `apps.taxonomy`
- categories and tags
- used for article filtering and recommendation signals

### `apps.notifications`
- create notification helper
- dropdown rendering and unread counts
- preference management
- conditional notification sending based on user settings

### `apps.api`
- REST endpoints for tracking and recommendations
- category onboarding API
- inline image upload API for article content

### `apps.core`
- shared base models and mixins
- application-wide utilities

## 9. Recommendation System in Detail

### 9.1 Model type

Blogora uses a **latent factor model** based on **TruncatedSVD**, which is a matrix factorization approach.

### 9.2 Input signals

The model uses implicit interactions instead of explicit 1-5 ratings.

Weights:
- likes are strongest (`3`)
- saves are moderate (`2`)
- article views are weaker (`1` + reading bonus)
- reading duration adds `0.5` per minute

### 9.3 Cold start handling

Cold-start uses explicit user preferences from `UserProfile.preferred_categories` and popular published articles.

### 9.4 Score boosting

The live prediction path also adds a `comment_count * 0.1` bonus to each article score, which favors articles with higher discussion engagement.

### 9.5 Filtering seen articles

Seen content is excluded using:
- `ArticleView` history
- `SavedArticle` history
- `Like` history

This improves recommendation novelty.

### 9.6 Model persistence

The SVD model is persisted with `joblib` at:
- `apps/recommendations/model/recommender.pkl`

### 9.7 When the model is missing

If no model file exists or the user is not in the trained model, the system gracefully falls back to preference-driven or popularity-based recommendations.

## 10. How to regenerate recommendations

### Train the ML model

Run inside Django shell or from a management command context:
```bash
python manage.py shell -c "from apps.recommendations.train_model import train; train()"
```

### Refresh precomputed recommendation scores

Run the management command:
```bash
python manage.py generate_recommendations --batch-size 100 --top-k 50
```

### Useful files
- `apps/recommendations/train_model.py`
- `apps/recommendations/feature_engineering.py`
- `apps/recommendations/predict.py`
- `apps/recommendations/models.py`
- `apps/recommendations/management/commands/generate_recommendations.py`

## 11. Notes and Observations

- The recommendation system is designed to combine offline precomputation with online scoring.
- The use of implicit signals is appropriate for a content platform where explicit ratings are rare.
- The cold-start path is simple but effective for new users, relying on category preferences.
- The `RecommendationScore` model allows a second layer of caching and batch refresh.
- Article view and reading tracking are fundamental to the recommendation logic and are captured with client-side JavaScript.

## 12. Suggested Improvements

- Add explicit tag-based scoring for new users using `preferred_tags`.
- Merge the two recommendation functions into a single coherent service layer.
- Add a normalization or weighting step for comment bonus and popularity to avoid skewed results.
- Expose an admin page for recommendation model status and last training run.
- Add a periodic Celery task to retrain and refresh recommendations automatically.

---

*Generated from the Blogora codebase and current recommendation implementation.*
