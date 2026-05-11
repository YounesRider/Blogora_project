import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = (
        'Export all users to a CSV file with username, email, role, staff status, superuser status, '
        'and optional plaintext password. Use --set-password to reset all passwords to a known value.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            default='user_credentials.csv',
            help='Output CSV file path (default: user_credentials.csv)'
        )
        parser.add_argument(
            '--set-password',
            default=None,
            help='If provided, reset all users to this password and export it in plaintext.'
        )

    def handle(self, *args, **options):
        output_path = Path(options['output'])
        set_password = options['set_password']

        users = User.objects.all().order_by('role', 'username')
        if not users.exists():
            self.stdout.write(self.style.WARNING('No users found in the database.'))
            return

        rows = []
        for user in users:
            password_value = 'UNUSABLE'
            if set_password is not None:
                user.set_password(set_password)
                user.save()
                password_value = set_password
            elif user.has_usable_password():
                password_value = 'UNKNOWN'  # Cannot recover hashed passwords

            rows.append([
                user.username,
                user.email,
                getattr(user, 'role', 'N/A'),
                str(user.is_staff),
                str(user.is_superuser),
                password_value,
            ])

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'username',
                'email',
                'role',
                'is_staff',
                'is_superuser',
                'password',
            ])
            writer.writerows(rows)

        self.stdout.write(self.style.SUCCESS(
            f'Exported {len(rows)} users to {output_path.resolve()}'
        ))
        if set_password is None:
            self.stdout.write(self.style.WARNING(
                'Passwords are marked UNKNOWN because hashed passwords cannot be recovered. '
                'Run this command again with --set-password <value> to set a known password for all users.'
            ))
