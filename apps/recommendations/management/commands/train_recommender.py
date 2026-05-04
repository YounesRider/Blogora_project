from django.core.management.base import BaseCommand
from apps.recommendations.train_model import train


class Command(BaseCommand):
    help = 'Entraîne le modèle de recommandation intelligent'

    def add_arguments(self, parser):
        parser.add_argument(
            '--components',
            type=int,
            default=50,
            help='Nombre de composantes pour le SVD (default: 50)'
        )

    def handle(self, *args, **options):
        self.stdout.write('🤖 Début de l\'entraînement du modèle de recommandation...')
        
        try:
            train(n_components=options['components'])
            self.stdout.write(
                self.style.SUCCESS('✅ Modèle entraîné avec succès !')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de l\'entraînement: {e}')
            )
