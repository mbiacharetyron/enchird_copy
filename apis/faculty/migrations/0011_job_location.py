# Generated by Django 4.2.7 on 2024-02-07 03:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faculty', '0010_job'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='location',
            field=models.CharField(default='Buea, Cameroon', max_length=100),
            preserve_default=False,
        ),
    ]
