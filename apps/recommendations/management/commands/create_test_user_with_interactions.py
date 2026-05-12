"""
Management command to create a test user with diverse interactions.
Usage: python manage.py create_test_user_with_interactions
"""
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db.models import Q
import random

from apps.users.models import User, UserProfile
from apps.blog.models import Article
from apps.taxonomy.models import Category
from apps.interactions.models import Like, SavedArticle, ArticleView, Reaction
from apps.comments.models import Comment


class Command(BaseCommand):
    help = 'Create a test user with diverse interactions for recommendation system testing'

    def handle(self, *args, **options):
        # Create test user
        username = 'test_recommender_user'
        email = 'test.recommender@blogora.test'
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': 'Test',
                'last_name': 'Recommender',
            }
        )
        
        if created:
            user.set_password('test123456')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created user: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'User already exists: {username}'))
        
        # Ensure UserProfile exists
        profile, profile_created = UserProfile.objects.get_or_create(user=user)
        
        # Get published articles
        articles = list(Article.objects.filter(status='published').order_by('-created_at')[:50])
        
        if not articles:
            self.stdout.write(self.style.WARNING('No published articles found. Run populate_data first.'))
            return
        
        # Get categories
        categories = list(Category.objects.all())
        
        # Set user category preferences (pick 3-5 random categories)
        if categories:
            preferred_cats = random.sample(categories, min(5, len(categories)))
            profile.preferred_categories.set(preferred_cats)
            self.stdout.write(f'✓ Set preferred categories: {", ".join(c.name for c in preferred_cats)}')
        
        # Create interactions
        article_content_type = ContentType.objects.get_for_model(Article)
        like_count = 0
        save_count = 0
        view_count = 0
        reaction_count = 0
        comment_count = 0
        
        # Sample articles for interactions (20-30 articles)
        interaction_articles = random.sample(articles, min(30, len(articles)))
        
        for idx, article in enumerate(interaction_articles):
            # Like some articles (60% chance)
            if random.random() < 0.6:
                like, created = Like.objects.get_or_create(
                    user=user,
                    content_type=article_content_type,
                    object_id=article.id
                )
                if created:
                    like_count += 1
            
            # Save some articles (40% chance)
            if random.random() < 0.4:
                save, created = SavedArticle.objects.get_or_create(
                    user=user,
                    article=article
                )
                if created:
                    save_count += 1
            
            # View all interaction articles with varied reading duration
            reading_duration = random.randint(30, 600)  # 30 seconds to 10 minutes
            view, created = ArticleView.objects.get_or_create(
                user=user,
                article=article,
                defaults={'reading_duration': reading_duration}
            )
            if created:
                view_count += 1
            
            # Add reactions to some articles (30% chance)
            if random.random() < 0.3:
                reaction_type = random.choice([choice[0] for choice in Reaction.ReactionType.choices])
                reaction, created = Reaction.objects.get_or_create(
                    user=user,
                    article=article,
                    reaction_type=reaction_type
                )
                if created:
                    reaction_count += 1
            
            # Add comments to some articles (15% chance)
            if random.random() < 0.15:
                Comment.objects.get_or_create(
                    author=user,
                    article=article,
                    defaults={
                        'content': f'Great article! This is a test comment #{idx+1}.',
                        'is_approved': True
                    }
                )
                comment_count += 1
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== Interactions Created ==='))
        self.stdout.write(f'Likes:     {like_count}')
        self.stdout.write(f'Saves:     {save_count}')
        self.stdout.write(f'Views:     {view_count}')
        self.stdout.write(f'Reactions: {reaction_count}')
        self.stdout.write(f'Comments:  {comment_count}')
        self.stdout.write(f'\nTotal interactions: {like_count + save_count + view_count + reaction_count + comment_count}')
        self.stdout.write(self.style.SUCCESS(f'\n✓ Test user ready for recommendation system: {email}'))
        self.stdout.write('Run the recommendation experiments with this user for validation.')
