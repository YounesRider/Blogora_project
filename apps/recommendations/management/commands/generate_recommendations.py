"""
Management command to generate recommendations with scores.
Usage: python manage.py generate_recommendations [--user-id=<id>] [--username=<username>] [--top-k=10]
       python manage.py generate_recommendations --username test_recommender_user --csv
"""
from django.core.management.base import BaseCommand
import joblib
import numpy as np
from pathlib import Path

from apps.users.models import User
from apps.blog.models import Article


class Command(BaseCommand):
    help = 'Generate predictions with scores for a user (id,score format)'

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, help='User ID to get recommendations for')
        parser.add_argument('--username', type=str, help='Username to get recommendations for')
        parser.add_argument('--top-k', type=int, default=10, help='Number of recommendations')
        parser.add_argument('--csv', action='store_true', help='Output as CSV format only (no header)')

    def handle(self, *args, **options):
        # Get user
        user_id = options.get('user_id')
        username = options.get('username')
        top_k = options.get('top_k', 10)
        csv_format = options.get('csv', False)
        
        if username:
            try:
                user = User.objects.get(username=username)
                user_id = user.id
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User not found: {username}'))
                return
        elif user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User not found: {user_id}'))
                return
        else:
            self.stdout.write(self.style.ERROR('Provide --user-id or --username'))
            return
        
        # Load model
        MODEL_PATH = Path(__file__).parent.parent.parent / "model" / "recommender.pkl"
        
        if not MODEL_PATH.exists():
            self.stdout.write(self.style.ERROR(f'Model not found: {MODEL_PATH}'))
            return
        
        model = joblib.load(MODEL_PATH)
        
        # Get predictions
        user_idx = model["user_idx"]
        
        if user_id not in user_idx:
            if not csv_format:
                self.stdout.write(self.style.WARNING(f'User {user.username} not in trained model. Using fallback.'))
            # Fallback: recommend popular articles
            articles = Article.objects.filter(status='published').order_by('-view_count')[:top_k]
            recommendations = [(a.id, 0.0) for a in articles]
        else:
            # Get user vector and compute scores
            i = user_idx[user_id]
            user_vec = model["user_factors"][i]
            scores = model["article_factors"] @ user_vec
            
            # Get top k
            top_indices = np.argsort(scores)[::-1][:top_k]
            article_ids = model["article_ids"]
            
            recommendations = [
                (int(article_ids[idx]), float(scores[idx]))
                for idx in top_indices
            ]
        
        # Output
        if csv_format:
            for article_id, score in recommendations:
                self.stdout.write(f"{article_id},{score:.6f}")
        else:
            self.stdout.write(f"\nRecommendations for {user.username} (top {top_k}):\n")
            self.stdout.write("id,score")
            for article_id, score in recommendations:
                self.stdout.write(f"{article_id},{score:.6f}")
            self.stdout.write(f"\nTotal: {len(recommendations)} recommendations")
