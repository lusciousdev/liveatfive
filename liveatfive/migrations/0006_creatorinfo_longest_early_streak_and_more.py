# Generated by Django 4.2.9 on 2024-03-16 04:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('liveatfive', '0005_creatorinfo_average_offset'),
    ]

    operations = [
        migrations.AddField(
            model_name='creatorinfo',
            name='longest_early_streak',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='creatorinfo',
            name='longest_late_streak',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='creatorinfo',
            name='longest_ontime_streak',
            field=models.IntegerField(default=0),
        ),
    ]
