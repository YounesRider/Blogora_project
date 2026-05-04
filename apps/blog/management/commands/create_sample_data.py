from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.blog.models import Article
from apps.taxonomy.models import Category, Tag
from apps.users.models import UserProfile
import random
from faker import Faker

User = get_user_model()
fake = Faker('fr_FR')


class Command(BaseCommand):
    help = 'Crée des données de test pour le blog intelligent'

    def add_arguments(self, parser):
        parser.add_argument(
            '--articles',
            type=int,
            default=50,
            help='Nombre d\'articles à créer (default: 50)'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Nombre d\'utilisateurs à créer (default: 10)'
        )

    def handle(self, *args, **options):
        articles_count = options['articles']
        users_count = options['users']
        
        self.stdout.write('Création des données de test...')
        
        # Créer des catégories
        categories_data = [
            'Technologie', 'Intelligence Artificielle', 'Développement Web',
            'Data Science', 'Cybersécurité', 'Cloud Computing', 'Mobile',
            'Blockchain', 'IoT', 'DevOps'
        ]
        
        for cat_name in categories_data:
            Category.objects.get_or_create(
                name=cat_name,
                defaults={'description': f'Articles sur {cat_name}'}
            )
        
        categories = list(Category.objects.all())
        self.stdout.write(f'{len(categories)} catégories créées')
        
        # Créer des tags
        tags_data = [
            'python', 'django', 'javascript', 'react', 'vue', 'machine-learning',
            'deep-learning', 'nlp', 'computer-vision', 'kubernetes', 'docker',
            'aws', 'azure', 'gcp', 'security', 'privacy', 'api', 'microservices',
            'testing', 'agile', 'startup', 'innovation', 'research', 'tutorial'
        ]
        
        for tag_name in tags_data:
            Tag.objects.get_or_create(name=tag_name)
        
        tags = list(Tag.objects.all())
        self.stdout.write(f'{len(tags)} tags créés')
        
        # Créer des utilisateurs
        created_users = []
        for i in range(users_count):
            username = f"user_{i+1}"
            email = f"user_{i+1}@example.com"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'bio': fake.sentence(),
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
                
                # Créer le profil
                profile, created = UserProfile.objects.get_or_create(user=user)
                
                # Ajouter des préférences aléatoires
                preferred_cats = random.sample(categories, random.randint(1, 3))
                preferred_tags = random.sample(tags, random.randint(2, 5))
                profile.preferred_categories.set(preferred_cats)
                profile.preferred_tags.set(preferred_tags)
                
                created_users.append(user)
        
        self.stdout.write(f'✅ {len(created_users)} utilisateurs créés')
        
        # Créer des articles
        articles_created = 0
        for i in range(articles_count):
            author = random.choice(created_users + [User.objects.get(username='admin')])
            category = random.choice(categories)
            
            # Générer le contenu
            title = fake.sentence().rstrip('.')
            excerpt = fake.paragraph()
            
            # Contenu plus structuré
            body_parts = [
                f"# {title}\n\n",
                f"{fake.paragraph()}\n\n",
                "## Introduction\n\n",
                f"{fake.paragraph()}\n\n",
                f"{fake.paragraph()}\n\n",
                "## Développement\n\n",
                f"{fake.paragraph()}\n\n",
                f"```python\n# Exemple de code\ndef hello_world():\n    print('Hello, World!')\n```\n\n",
                f"{fake.paragraph()}\n\n",
                "## Conclusion\n\n",
                f"{fake.paragraph()}\n",
            ]
            body = ''.join(body_parts)
            
            article = Article.objects.create(
                title=title,
                slug=fake.slug(),
                excerpt=excerpt,
                body=body,
                author=author,
                category=category,
                status='published',
                published_at=timezone.now() - timezone.timedelta(days=random.randint(1, 365)),
                meta_title=title[:70],
                meta_description=excerpt[:160],
                is_featured=random.random() < 0.1,  # 10% d'articles en vedette
            )
            
            # Ajouter des tags
            article_tags = random.sample(tags, random.randint(2, 5))
            article.tags.set(article_tags)
            
            # Simuler des vues
            article.view_count = random.randint(10, 1000)
            article.save()
            
            articles_created += 1
            
            if articles_created % 10 == 0:
                self.stdout.write(f'📝 {articles_created}/{articles_count} articles créés...')
        
        self.stdout.write(self.style.SUCCESS(f'✅ {articles_created} articles créés !'))
        
        # Créer des interactions
        self.stdout.write('💕 Création des interactions...')
        
        from apps.interactions.models import Like, SavedArticle, ArticleView
        
        # Likes
        for user in created_users:
            articles_to_like = random.sample(list(Article.objects.all()), random.randint(5, 20))
            for article in articles_to_like:
                Like.objects.get_or_create(user=user, article=article)
        
        # Sauvegardes
        for user in created_users:
            articles_to_save = random.sample(list(Article.objects.all()), random.randint(3, 15))
            for article in articles_to_save:
                SavedArticle.objects.get_or_create(user=user, article=article)
        
        # Vues
        all_articles = list(Article.objects.all())
        for user in created_users:
            if all_articles:
                view_count = min(random.randint(5, 15), len(all_articles))
                articles_to_view = random.sample(all_articles, view_count)
                for article in articles_to_view:
                    ArticleView.objects.get_or_create(
                        user=user,
                        article=article,
                        defaults={
                            'reading_duration': random.randint(30, 600),  # 30s à 10min
                            'ip_address': fake.ipv4(),
                            'user_agent': fake.user_agent()
                        }
                    )
        
        self.stdout.write(self.style.SUCCESS('🎉 Données de test créées avec succès !'))
        self.stdout.write('📊 Statistiques:')
        self.stdout.write(f'   • {User.objects.count()} utilisateurs')
        self.stdout.write(f'   • {Article.objects.count()} articles')
        self.stdout.write(f'   • {Like.objects.count()} likes')
        self.stdout.write(f'   • {SavedArticle.objects.count()} sauvegardes')
        self.stdout.write(f'   • {ArticleView.objects.count()} vues')
        
        self.stdout.write(self.style.SUCCESS('\n🚀 Vous pouvez maintenant lancer le serveur: python manage.py runserver'))
        self.stdout.write('👤 Admin: admin / password123')
