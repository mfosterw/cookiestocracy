# Generated by Django 4.2.9 on 2024-02-19 06:04

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("django_celery_beat", "0018_improve_crontab_helptext"),
        ("webiscite", "0008_alter_bill_description_alter_pullrequest_pr_num_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="vote",
            old_name="timestamp",
            new_name="time_created",
        ),
        migrations.RemoveField(
            model_name="bill",
            name="prop_date",
        ),
        migrations.RemoveField(
            model_name="pullrequest",
            name="prop_date",
        ),
        migrations.AddField(
            model_name="bill",
            name="submit_task",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="django_celery_beat.periodictask",
            ),
        ),
        migrations.AddField(
            model_name="bill",
            name="time_created",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="bill",
            name="time_updated",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="pullrequest",
            name="time_created",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="pullrequest",
            name="time_updated",
            field=models.DateTimeField(auto_now=True),
        ),
    ]