# Generated by Django 4.2.11 on 2024-09-03 00:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('liveatfive', '0006_creatorinfo_longest_early_streak_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='twitchvideo',
            name='vod_id',
            field=models.CharField(default='', max_length=128, unique=True),
        ),
    ]