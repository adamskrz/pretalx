# Generated by Django 5.1.7 on 2025-04-30 10:21

import pretalx.common.models.file
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0005_auto_20180202_1116"),
    ]

    operations = [
        migrations.CreateModel(
            name="CachedFile",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, primary_key=True, serialize=False
                    ),
                ),
                ("expires", models.DateTimeField()),
                ("timestamp", models.DateTimeField(blank=True, null=True)),
                ("filename", models.CharField(max_length=255)),
                ("content_type", models.CharField(max_length=255)),
                ("session_key", models.TextField(null=True)),
                (
                    "file",
                    models.FileField(
                        max_length=255,
                        null=True,
                        upload_to=pretalx.common.models.file.cachedfile_name,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["expires"], name="common_cach_expires_d8715c_idx"
                    )
                ],
            },
        ),
    ]
