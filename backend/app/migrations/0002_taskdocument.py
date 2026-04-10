"""
Migration to add TaskDocument model for task-aware search.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='app.document')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='app.task')),
            ],
            options={
                'db_table': 'task_documents',
            },
        ),
        migrations.AddIndex(
            model_name='taskdocument',
            index=models.Index(fields=['task'], name='task_docume_task_id_12345_idx'),
        ),
        migrations.AddIndex(
            model_name='taskdocument',
            index=models.Index(fields=['document'], name='task_docume_document_12345_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='taskdocument',
            unique_together={('task', 'document')},
        ),
    ]
