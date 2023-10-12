# Generated by Django 4.2.6 on 2023-10-12 01:40

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Vacancy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.TextField(max_length=500)),
                ('title', models.CharField(max_length=250, verbose_name='Name vacancy')),
                ('company', models.CharField(max_length=250, verbose_name='Company')),
                ('description', models.TextField(verbose_name='Vacancy description')),
                ('search_source', models.CharField(max_length=250, verbose_name='Search source')),
                ('timestamp', models.DateField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Job vacancy',
                'verbose_name_plural': 'Vacancies',
                'ordering': ['-timestamp'],
            },
        ),
    ]