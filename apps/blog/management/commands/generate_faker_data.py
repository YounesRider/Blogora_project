from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone
from django.core.files.base import ContentFile
from faker import Faker
from PIL import Image, ImageDraw, ImageFont
import random
from io import BytesIO
from datetime import timedelta
from apps.blog.models import Article
from apps.users.models import User, UserProfile
from apps.taxonomy.models import Category, Tag

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Generate realistic faker data with images for articles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=15,
            help='Number of users to create (default: 15)'
        )
        parser.add_argument(
            '--articles',
            type=int,
            default=50,
            help='Number of articles to create (default: 50)'
        )
        parser.add_argument(
            '--with-images',
            action='store_true',
            help='Generate placeholder images for articles'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting faker data generation...'))
        
        # Create categories and tags
        self.create_categories_and_tags()
        
        # Create users with roles
        self.create_users(options['users'])
        
        # Create articles with optional images
        self.create_articles(options['articles'], options['with_images'])
        
        self.stdout.write(self.style.SUCCESS('✅ Data generation completed successfully!'))

    def create_categories_and_tags(self):
        """Create blog categories and tags"""
        self.stdout.write('📁 Creating categories and tags...')
        
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
                self.stdout.write(f'  ✓ Created category: {category.name}')
        
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
                defaults={'name': tag_name.replace('-', ' ').title()}
            )
            if created:
                self.stdout.write(f'  ✓ Created tag: {tag.name}')

    def create_users(self, count):
        """Create users with author and reader roles"""
        self.stdout.write(f'👥 Creating {count} users...')
        
        categories = list(Category.objects.all())
        
        for i in range(count):
            username = f"user_{fake.user_name()}_{i}".lower()[:30]
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
                user.set_password('password123')
                
                # Assign roles
                if i == 0:
                    user.role = User.Role.ADMIN
                elif i < count // 3:
                    user.role = User.Role.AUTHOR
                else:
                    user.role = User.Role.USER
                
                user.save()
                
                # Create user profile
                profile, _ = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'bio': fake.paragraph(nb_sentences=2),
                        'location': fake.city(),
                        'auto_publish': user.role in [User.Role.AUTHOR, User.Role.ADMIN],
                    }
                )
                
                # Add preferred categories
                if categories:
                    preferred_categories = random.sample(
                        categories,
                        random.randint(1, min(3, len(categories)))
                    )
                    profile.preferred_categories.set(preferred_categories)
                
                self.stdout.write(
                    f'  ✓ {user.username} ({user.get_role_display()})'
                )

    def generate_placeholder_image(self, title, width=800, height=600):
        """Generate a placeholder image for article cover"""
        # Random color palette
        colors = [
            (52, 152, 219),    # Blue
            (46, 204, 113),    # Green
            (155, 89, 182),    # Purple
            (230, 126, 34),    # Orange
            (231, 76, 60),     # Red
            (41, 128, 185),    # Dark Blue
            (22, 160, 133),    # Teal
            (44, 62, 80),      # Dark Gray
        ]
        
        bg_color = random.choice(colors)
        text_color = (255, 255, 255)
        
        # Create image
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Add text
        try:
            # Try to use a larger font if available
            font_size = 48
            font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Wrap text
        text = title[:50]
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Center text
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill=text_color, font=font)
        
        # Convert to file
        img_io = BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)
        
        return ContentFile(img_io.getvalue(), name='cover.jpg')

    def create_articles(self, count, with_images=False):
        """Create articles with faker data"""
        self.stdout.write(f'📝 Creating {count} articles...')
        
        authors = list(User.objects.filter(role__in=[User.Role.AUTHOR, User.Role.ADMIN]))
        categories = list(Category.objects.all())
        tags = list(Tag.objects.all())
        
        if not authors:
            self.stdout.write(self.style.WARNING('  ⚠️  No authors found. Create authors first!'))
            return
        
        # Article titles
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
        ]
        
        for i in range(min(count, len(article_titles))):
            author = random.choice(authors)
            title = article_titles[i % len(article_titles)]
            
            # Generate unique slug
            base_slug = slugify(title)
            slug = base_slug
            counter = 1
            while Article.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Generate content
            content = fake.paragraph(nb_sentences=random.randint(10, 20)) + '\n\n'
            content += '\n\n'.join([
                fake.paragraph(nb_sentences=random.randint(5, 10))
                for _ in range(random.randint(3, 6))
            ])
            
            article = Article.objects.create(
                author=author,
                title=title,
                slug=slug,
                content=content,
                status=random.choice(['published', 'published', 'published', 'draft']),
                view_count=random.randint(0, 5000),
                created_at=fake.date_time_between(start_date='-6m', end_date='now'),
                updated_at=fake.date_time_between(start_date='-3m', end_date='now')
            )
            
            # Add categories
            if categories:
                article_categories = random.sample(
                    categories,
                    random.randint(1, min(3, len(categories)))
                )
                article.categories.set(article_categories)
            
            # Add tags
            if tags:
                article_tags = random.sample(
                    tags,
                    random.randint(2, min(6, len(tags)))
                )
                article.tags.set(article_tags)
            
            # Add cover image if requested
            if with_images:
                try:
                    cover_image = self.generate_placeholder_image(title)
                    article.cover_image.save(f'cover_{slug}.jpg', cover_image, save=True)
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  Could not generate image for {title}: {str(e)}')
                    )
            
            # Set published_at for published articles
            if article.status == 'published':
                article.published_at = article.created_at + timedelta(days=random.randint(0, 7))
                article.save()
            
            self.stdout.write(f'  ✓ {title[:50]}...')
        
        self.stdout.write(self.style.SUCCESS(f'  Created {min(count, len(article_titles))} articles'))
