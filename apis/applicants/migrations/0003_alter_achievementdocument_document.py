# Generated by Django 4.2.7 on 2023-12-14 23:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applicants', '0002_applicant_is_selected'),
    ]

    operations = [
        migrations.AlterField(
            model_name='achievementdocument',
            name='document',
            field=models.CharField(max_length=255),
        ),
    ]
