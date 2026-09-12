# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = []  # type: ignore

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                (
                    'id',
                    models.AutoField(
                        verbose_name='ID',
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ('title', models.CharField(max_length=100)),
                ('body', models.TextField()),
                (
                    'status',
                    models.CharField(
                        default=b'draft',
                        max_length=10,
                        choices=[(b'draft', 'Draft'), (b'published', 'Published')],
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='Author',
            fields=[
                (
                    'id',
                    models.AutoField(
                        verbose_name='ID',
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='article',
            name='author',
            field=models.ForeignKey(to='blog.Author', on_delete=models.CASCADE),
        ),
    ]
