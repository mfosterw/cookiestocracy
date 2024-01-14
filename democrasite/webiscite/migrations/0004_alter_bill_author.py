# Generated by Django 4.2.9 on 2024-01-14 00:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("webiscite", "0003_alter_bill_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bill",
            name="author",
            field=models.ForeignKey(
                default=34, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL
            ),
            preserve_default=False,
        ),
    ]