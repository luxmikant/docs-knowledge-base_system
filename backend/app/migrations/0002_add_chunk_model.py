# Generated migration for adding Chunk model

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Chunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chunk_index', models.IntegerField()),
                ('chunk_text', models.TextField()),
                ('token_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='app.document')),
            ],
            options={
                'db_table': 'chunks',
                'ordering': ['document', 'chunk_index'],
            },
        ),
        migrations.AddIndex(
            model_name='chunk',
            index=models.Index(fields=['document'], name='chunks_document_idx'),
        ),
        migrations.AddIndex(
            model_name='chunk',
            index=models.Index(fields=['created_at'], name='chunks_created_at_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='chunk',
            unique_together={('document', 'chunk_index')},
        ),
    ]
