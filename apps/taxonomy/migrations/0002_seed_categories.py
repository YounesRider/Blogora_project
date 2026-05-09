from django.db import migrations


def seed_categories(apps, schema_editor):
    Category = apps.get_model("taxonomy", "Category")
    categories = [
        ("technology", "Technology", "General technology news and tutorials"),
        ("artificial-intelligence", "Artificial Intelligence", "AI, ML, LLMs, and practical applications"),
        ("web-development", "Web Development", "Frontend, backend, and full-stack development"),
        ("data-science", "Data Science", "Data analysis, visualization, and modeling"),
        ("cybersecurity", "Cybersecurity", "Security best practices and threat analysis"),
    ]
    for slug, name, description in categories:
        category, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "description": description},
        )
        if category.name != name or category.description != description:
            category.name = name
            category.description = description
            category.save(update_fields=["name", "description"])


class Migration(migrations.Migration):
    dependencies = [
        ("taxonomy", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
    ]
