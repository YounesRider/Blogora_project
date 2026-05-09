from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.recommendations.models import RecommendationScore
from apps.recommendations.predict import get_recommendations
from apps.users.models import User


def generate_user_recommendations(user_id: int, top_k: int = 50) -> int:
    user = User.objects.filter(id=user_id).first()
    if not user:
        return 0

    RecommendationScore.objects.filter(user=user).delete()
    recommended_ids = get_recommendations(user.id, top_k=top_k, exclude_seen=True)
    scores = []
    for rank, article_id in enumerate(recommended_ids):
        score = 1.0 - (rank / max(top_k, 1))
        scores.append(RecommendationScore(user=user, article_id=article_id, score=score))
    RecommendationScore.objects.bulk_create(scores, ignore_conflicts=True)
    return len(scores)


class Command(BaseCommand):
    help = 'Génère les scores de recommandation pour tous les utilisateurs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Taille du batch pour traiter les utilisateurs (default: 100)'
        )
        parser.add_argument(
            '--top-k',
            type=int,
            default=50,
            help='Nombre de recommandations par utilisateur (default: 50)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        top_k = options['top_k']
        
        self.stdout.write(f' Génération des recommandations (top-{top_k}) par batch de {batch_size}...')
        
        # Supprimer les anciens scores
        deleted_count = RecommendationScore.objects.all().delete()[0]
        self.stdout.write(f'  Supprimé {deleted_count} anciens scores')
        
        users = User.objects.all()
        total_users = users.count()
        processed = 0
        
        for i in range(0, total_users, batch_size):
            batch = users[i:i + batch_size]
            
            for user in batch:
                try:
                    # Obtenir les recommandations
                    recommended_ids = get_recommendations(
                        user.id, 
                        top_k=top_k, 
                        exclude_seen=True
                    )
                    
                    # Créer les scores
                    scores = []
                    for rank, article_id in enumerate(recommended_ids):
                        # Score décroissant basé sur le rang
                        score = 1.0 - (rank / top_k)
                        scores.append(RecommendationScore(
                            user=user,
                            article_id=article_id,
                            score=score
                        ))
                    
                    # Création en masse
                    RecommendationScore.objects.bulk_create(scores, ignore_conflicts=True)
                    processed += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Erreur utilisateur {user.id}: {e}')
                    )
            
            self.stdout.write(
                f'📊 Traités {min(i + batch_size, total_users)}/{total_users} utilisateurs...'
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Terminé ! {processed} utilisateurs traités')
        )
