from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from django.utils import timezone
from faker import Faker
import random
from datetime import timedelta
from apps.blog.models import Article
from apps.users.models import User, UserProfile
from apps.taxonomy.models import Category, Tag
from apps.core.models import Collection
from apps.comments.models import Comment
from apps.interactions.models import Like
from apps.notifications.models import Notification

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Populate the database with realistic fake data'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=20, help='Number of users to create')
        parser.add_argument('--articles', type=int, default=50, help='Number of articles to create')
        parser.add_argument('--comments', type=int, default=200, help='Number of comments to create')

    def handle(self, *args, **options):
        self.stdout.write('Starting data population...')
        
        # Create categories and tags first
        self.create_categories_and_tags()
        
        # Create users
        self.create_users(options['users'])
        
        # Create articles
        self.create_articles(options['articles'])
        
        # Create comments
        self.create_comments(options['comments'])
        
        # Create interactions
        self.create_interactions()
        
        # Create collections
        self.create_collections()
        
        # Create notifications
        self.create_notifications()
        
        self.stdout.write(self.style.SUCCESS('Data population completed successfully!'))

    def create_categories_and_tags(self):
        """Create realistic blog categories and tags"""
        self.stdout.write('Creating categories and tags...')
        
        categories_data = [
            {'name': 'Technology', 'description': 'Latest tech news, reviews, and tutorials'},
            {'name': 'Programming', 'description': 'Coding tutorials, best practices, and development tips'},
            {'name': 'Web Development', 'description': 'Frontend, backend, and full-stack development'},
            {'name': 'Data Science', 'description': 'Machine learning, AI, and data analysis'},
            {'name': 'Mobile Development', 'description': 'iOS, Android, and cross-platform apps'},
            {'name': 'DevOps', 'description': 'Infrastructure, deployment, and operations'},
            {'name': 'Cybersecurity', 'description': 'Security best practices and threat analysis'},
            {'name': 'Cloud Computing', 'description': 'AWS, Azure, GCP, and cloud architecture'},
            {'name': 'Design', 'description': 'UI/UX, graphic design, and creative workflows'},
            {'name': 'Business', 'description': 'Startups, entrepreneurship, and business strategy'},
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=slugify(cat_data['name']),
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'  Created category: {category.name}')
        
        tags_data = [
            'python', 'javascript', 'react', 'vue', 'angular', 'django', 'flask', 'nodejs',
            'machine-learning', 'artificial-intelligence', 'data-science', 'web-development',
            'mobile-apps', 'ios', 'android', 'flutter', 'react-native', 'aws', 'docker',
            'kubernetes', 'devops', 'cybersecurity', 'blockchain', 'cryptocurrency',
            'startup', 'entrepreneurship', 'ux-design', 'ui-design', 'productivity',
            'remote-work', 'agile', 'scrum', 'testing', 'api', 'microservices',
            'database', 'sql', 'nosql', 'postgresql', 'mongodb', 'redis',
            'git', 'github', 'gitlab', 'ci-cd', 'automation', 'security', 'privacy'
        ]
        
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(
                slug=slugify(tag_name),
                defaults={'name': tag_name}
            )
            if created:
                self.stdout.write(f'  Created tag: {tag.name}')

    def create_users(self, count):
        """Create realistic user profiles"""
        self.stdout.write(f'Creating {count} users...')
        
        # Get all categories for user preferences
        categories = list(Category.objects.all())
        
        for i in range(count):
            # Create user
            username = fake.user_name() + str(i)
            email = fake.email()
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'is_active': True,
                }
            )
            
            if created:
                user.set_password('password123')  # Default password for testing
                user.save()
            
            # Get or create user profile
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'bio': fake.paragraph(),
                    'website': fake.url(),
                    'twitter': fake.user_name(),
                    'github': fake.user_name(),
                    'location': fake.city() + ', ' + fake.country(),
                    'social_links': {
                        'twitter': f'https://twitter.com/{fake.user_name()}',
                        'github': f'https://github.com/{fake.user_name()}',
                        'linkedin': f'https://linkedin.com/in/{fake.user_name()}'
                    },
                    'auto_publish': random.choice([True, False]),
                    'requested_author': random.choice([True, False])
                }
            )
            
            # Set user role
            if i == 0:
                user.role = User.Role.ADMIN
            elif i < 5:
                user.role = User.Role.AUTHOR
            else:
                user.role = random.choice([User.Role.USER, User.Role.AUTHOR])
            user.save()
            
            # Add preferred categories
            preferred_categories = random.sample(categories, random.randint(1, 4))
            profile.preferred_categories.set(preferred_categories)
            
            self.stdout.write(f'  Created user: {user.username} ({user.get_role_display()})')

    def create_articles(self, count):
        """Create realistic blog articles"""
        self.stdout.write(f'Creating {count} articles...')
        
        authors = User.objects.filter(role__in=[User.Role.AUTHOR, User.Role.ADMIN])
        categories = list(Category.objects.all())
        tags = list(Tag.objects.all())
        
        article_titles = [
            "Getting Started with Django REST Framework",
            "10 JavaScript Tips Every Developer Should Know",
            "Building Scalable Microservices with Docker",
            "The Future of Artificial Intelligence in Web Development",
            "Understanding React Hooks: A Complete Guide",
            "Python Best Practices for Clean Code",
            "Introduction to Machine Learning with Python",
            "Securing Your Web Application: Top 10 Tips",
            "Cloud Migration Strategies for Modern Applications",
            "The Ultimate Guide to Vue.js 3",
            "Database Design Patterns for Scalability",
            "Mobile App Development: React Native vs Flutter",
            "DevOps Automation: Tools and Techniques",
            "Cybersecurity Essentials for Developers",
            "Building RESTful APIs with Node.js",
            "Frontend Performance Optimization Techniques",
            "Data Visualization with D3.js",
            "Kubernetes: A Beginner's Guide",
            "The Psychology of User Experience Design",
            "Agile Methodologies: Scrum vs Kanban",
            "Machine Learning in Production: Best Practices",
            "Web Accessibility: Why It Matters",
            "GraphQL vs REST: Which to Choose?",
            "Building Real-time Applications with WebSockets",
            "The Rise of Low-Code Development Platforms",
            "Cloud Native Architecture Patterns",
            "Mobile First Design Principles",
            "Database Optimization Techniques",
            "API Security Best Practices",
            "The Future of Web Development",
            "Building Progressive Web Apps",
            "Understanding Container Orchestration",
            "Data Privacy in the Age of Big Data",
            "Microservices vs Monolithic Architecture",
            "The Importance of Code Documentation",
            "Building Scalable Frontend Applications",
            "Introduction to Blockchain Technology",
            "Cloud Cost Optimization Strategies",
            "The Impact of AI on Software Development",
            "Building Resilient Distributed Systems",
            "Modern CSS Techniques for 2024",
            "Database Sharding Strategies",
            "The Evolution of JavaScript Frameworks",
            "Building Secure Authentication Systems",
            "Cloud Native Development Practices",
            "The Role of DevOps in Modern Development",
            "Introduction to Serverless Architecture",
            "Building High-Performance Web Applications",
            "The Future of Mobile Development",
            "Data Engineering Best Practices",
            "Understanding Cloud Security",
            "Building API Gateways and Service Meshes",
            "The Importance of Testing in Development",
            "Modern Frontend Build Tools",
            "Building Scalable Data Pipelines"
        ]
        
        for i in range(min(count, len(article_titles))):
            author = random.choice(authors)
            title = article_titles[i]
            
            # Generate content
            content = fake.paragraph(nb_sentences=random.randint(10, 30))
            for _ in range(random.randint(3, 8)):
                content += '\n\n' + fake.paragraph(nb_sentences=random.randint(5, 15))
            
            # Ensure unique slug
            base_slug = slugify(title)
            slug = base_slug
            counter = 1
            while Article.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            article = Article.objects.create(
                author=author,
                title=title,
                slug=slug,
                content=content,
                status=random.choice(['published', 'published', 'published', 'draft', 'pending_review']),
                auto_publish=random.choice([True, False]),
                view_count=random.randint(0, 10000),
                created_at=fake.date_time_between(start_date='-1y', end_date='now'),
                updated_at=fake.date_time_between(start_date='-6m', end_date='now')
            )
            
            # Add categories
            article_categories = random.sample(categories, random.randint(1, 3))
            article.categories.set(article_categories)
            
            # Add tags
            article_tags = random.sample(tags, random.randint(2, 6))
            for tag in article_tags:
                article.tags.add(tag)
            
            # Set published_at for published articles
            if article.status == 'published':
                article.published_at = article.created_at + timedelta(days=random.randint(0, 30))
                article.save()
            
            self.stdout.write(f'  Created article: {article.title}')

    def create_comments(self, count):
        """Create realistic comments"""
        self.stdout.write(f'Creating {count} comments...')
        
        users = list(User.objects.all())
        articles = list(Article.objects.filter(status='published'))
        
        for i in range(count):
            article = random.choice(articles)
            author = random.choice(users)
            
            # Create comment or reply
            parent = None
            if random.random() > 0.7 and Comment.objects.filter(article=article).exists():
                existing_comments = list(Comment.objects.filter(article=article))
                parent = random.choice(existing_comments)
            
            comment = Comment.objects.create(
                article=article,
                author=author,
                content=fake.paragraph(nb_sentences=random.randint(1, 5)),
                parent=parent,
                created_at=fake.date_time_between(start_date=article.created_at, end_date='now'),
                is_approved=True
            )
            
            self.stdout.write(f'  Created comment on: {article.title[:30]}...')

    def create_interactions(self):
        """Create likes and follows"""
        self.stdout.write('Creating interactions...')
        
        users = list(User.objects.all())
        articles = list(Article.objects.filter(status='published'))
        comments = list(Comment.objects.all())
        
        # Create likes for articles
        for user in users:
            # Like random articles
            liked_articles = random.sample(articles, random.randint(0, min(20, len(articles))))
            for article in liked_articles:
                if article.author != user:  # Don't like your own articles
                    Like.objects.get_or_create(
                        user=user,
                        content_type=ContentType.objects.get_for_model(Article),
                        object_id=article.id
                    )
        
        # Create likes for comments
        for user in users:
            # Like random comments
            liked_comments = random.sample(comments, random.randint(0, min(10, len(comments))))
            for comment in liked_comments:
                if comment.author != user:  # Don't like your own comments
                    Like.objects.get_or_create(
                        user=user,
                        content_type=ContentType.objects.get_for_model(Comment),
                        object_id=comment.id
                    )
        
        # Create follows
        for user in users:
            # Follow random users
            follow_count = random.randint(0, min(10, len(users)))
            following_users = random.sample([u for u in users if u != user], follow_count)
            for following_user in following_users:
                from apps.users.models import Follow
                Follow.objects.get_or_create(
                    follower=user,
                    following=following_user
                )
        
        self.stdout.write('  Created likes and follows')

    def create_collections(self):
        """Create user collections"""
        self.stdout.write('Creating collections...')
        
        users = list(User.objects.all())
        articles = list(Article.objects.filter(status='published'))
        
        for user in users:
            # Create 2-5 collections per user
            collection_count = random.randint(2, 5)
            
            # Always create a "Saved Posts" collection
            saved_collection, created = Collection.objects.get_or_create(
                owner=user,
                name="Saved Posts",
                defaults={
                    'description': 'My default collection for saved articles',
                    'is_private': True
                }
            )
            
            if created:
                # Add some articles to saved collection
                saved_articles = random.sample(articles, random.randint(5, 15))
                saved_collection.articles.set(saved_articles)
            
            # Create additional collections
            for i in range(collection_count - 1):
                collection_names = [
                    "Reading List", "Favorites", "To Read", "Tech Articles", "Design Inspiration",
                    "Learning Resources", "Work References", "Personal Projects", "Research",
                    "Tutorials", "Best Practices", "Case Studies", "Industry News"
                ]
                
                name = random.choice(collection_names)
                if Collection.objects.filter(owner=user, name=name).exists():
                    name = f"{name} {i+1}"
                
                collection = Collection.objects.create(
                    owner=user,
                    name=name,
                    description=fake.sentence(),
                    is_private=random.choice([True, False])
                )
                
                # Add some articles to collection
                collection_articles = random.sample(articles, random.randint(3, 10))
                collection.articles.set(collection_articles)
        
        self.stdout.write('  Created collections')

    def create_notifications(self):
        """Create sample notifications"""
        self.stdout.write('Creating notifications...')
        
        users = list(User.objects.all())
        articles = list(Article.objects.all())
        
        for user in users[:10]:  # Create notifications for first 10 users
            # Create various notification types
            notification_types = [
                ('article_approved', 'Your article has been approved!'),
                ('article_rejected', 'Your article needs revisions.'),
                ('new_follower', 'Someone started following you.'),
                ('comment_reply', 'Someone replied to your comment.'),
                ('article_liked', 'Someone liked your article.'),
            ]
            
            for _ in range(random.randint(2, 8)):
                notif_type, message = random.choice(notification_types)
                
                # Find a suitable sender
                if notif_type in ['article_approved', 'article_rejected']:
                    sender = User.objects.filter(role=User.Role.ADMIN).first()
                    if sender and sender == user:
                        continue
                else:
                    sender = random.choice([u for u in users if u != user])
                
                # Create notification
                notification = Notification.objects.create(
                    recipient=user,
                    sender=sender,
                    notification_type=notif_type,
                    message=message,
                    is_read=random.choice([True, False])
                )
                
                # Link to content if applicable
                if notif_type in ['article_approved', 'article_rejected', 'article_liked']:
                    user_articles = Article.objects.filter(author=user)
                    if user_articles.exists():
                        notification.content_object = random.choice(user_articles)
                        notification.save()
        
        self.stdout.write('  Created notifications')
