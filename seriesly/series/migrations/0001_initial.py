# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Episode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('season_number', models.IntegerField(default=0)),
                ('number', models.IntegerField(default=0)),
                ('title', models.CharField(max_length=255)),
                ('text', models.TextField()),
                ('date', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.IntegerField()),
                ('start', models.DateTimeField(null=True)),
                ('end', models.DateTimeField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Show',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('ordered_name', models.CharField(max_length=255)),
                ('normalized_name', models.CharField(max_length=255)),
                ('alt_names', models.TextField()),
                ('slug', models.SlugField()),
                ('description', models.TextField()),
                ('genres', models.CharField(max_length=255)),
                ('network', models.CharField(max_length=255)),
                ('active', models.BooleanField(default=True)),
                ('country', models.CharField(max_length=255)),
                ('runtime', models.IntegerField()),
                ('timezone', models.CharField(max_length=255)),
                ('provider_id', models.IntegerField()),
                ('added', models.DateTimeField()),
            ],
        ),
        migrations.AddField(
            model_name='season',
            name='show',
            field=models.ForeignKey(to='series.Show'),
        ),
        migrations.AddField(
            model_name='episode',
            name='season',
            field=models.ForeignKey(to='series.Season', null=True),
        ),
        migrations.AddField(
            model_name='episode',
            name='show',
            field=models.ForeignKey(to='series.Show'),
        ),
    ]
