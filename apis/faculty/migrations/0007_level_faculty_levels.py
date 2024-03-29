# Generated by Django 4.2.7 on 2024-01-09 02:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('faculty', '0006_department_about_department_description_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Level',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='faculty',
            name='levels',
            field=models.ManyToManyField(blank=True, null=True, to='faculty.level'),
        ),
    ]
