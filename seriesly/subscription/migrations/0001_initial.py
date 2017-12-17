# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('series', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subkey', models.CharField(max_length=255)),
                ('last_visited', models.DateTimeField(null=True)),
                ('last_changed', models.DateTimeField(null=True)),
                ('activated_mail', models.BooleanField(default=False)),
                ('email', models.CharField(max_length=255, blank=True)),
                ('activated_xmpp', models.BooleanField(default=False)),
                ('xmpp', models.CharField(max_length=255, blank=True)),
                ('settings', models.TextField(blank=True)),
                ('webhook', models.CharField(max_length=255, blank=True)),
                ('public_id', models.CharField(max_length=255, blank=True)),
                ('feed_cache', models.TextField(blank=True)),
                ('feed_stamp', models.DateTimeField(null=True, blank=True)),
                ('calendar_cache', models.TextField(blank=True)),
                ('calendar_stamp', models.DateTimeField(null=True, blank=True)),
                ('feed_public_cache', models.TextField(blank=True)),
                ('feed_public_stamp', models.DateTimeField(null=True, blank=True)),
                ('show_cache', models.TextField(blank=True)),
                ('next_airtime', models.DateTimeField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='SubscriptionItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('show', models.ForeignKey(to='series.Show', on_delete=models.CASCADE)),
                ('subscription', models.ForeignKey(to='subscription.Subscription', on_delete=models.CASCADE)),
            ],
        ),
    ]
