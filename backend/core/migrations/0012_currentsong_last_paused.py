# Generated by Django 2.2.20 on 2021-07-02 19:50

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [("core", "0011_auto_20210427_1339")]

    operations = [
        migrations.AddField(
            model_name="currentsong",
            name="last_paused",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        )
    ]
