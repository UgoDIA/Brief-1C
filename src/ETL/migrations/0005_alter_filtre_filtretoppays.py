# Generated by Django 4.1.3 on 2022-12-13 06:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ETL', '0004_filtre_filtretoppays'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filtre',
            name='filtretoppays',
            field=models.CharField(blank=True, db_column='filtreTopPays', max_length=30, null=True),
        ),
    ]