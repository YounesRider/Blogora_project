from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_user_role_moderator'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='email_notifications',
            field=models.BooleanField(default=True, help_text='Receive email notifications for important updates'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='push_notifications',
            field=models.BooleanField(default=True, help_text='Receive in-app push notifications'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='notify_article_comments',
            field=models.BooleanField(default=True, help_text='Notify me when someone comments on my article'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='notify_comment_replies',
            field=models.BooleanField(default=True, help_text='Notify me when someone replies to my comment'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='notify_article_likes',
            field=models.BooleanField(default=True, help_text='Notify me when someone likes my article'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='notify_article_saves',
            field=models.BooleanField(default=True, help_text='Notify me when someone saves my article'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='notify_comment_likes',
            field=models.BooleanField(default=True, help_text='Notify me when someone likes my comment'),
        ),
    ]
