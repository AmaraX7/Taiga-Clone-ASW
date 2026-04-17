from django.db import migrations, models


def forwards(apps, schema_editor):
    Issue = apps.get_model('issues', 'Issue')

    for issue in Issue.objects.select_related('issue_type', 'priority', 'severity').all():
        issue_type_slug = 'bug'
        priority_slug = 'normal'
        severity_slug = 'normal'

        if issue.issue_type_id and issue.issue_type:
            issue_type_slug = issue.issue_type.slug
        if issue.priority_id and issue.priority:
            priority_slug = issue.priority.slug
        if issue.severity_id and issue.severity:
            severity_slug = issue.severity.slug

        issue.issue_type_slug = issue_type_slug
        issue.priority_slug = priority_slug
        issue.severity_slug = severity_slug
        issue.save(update_fields=['issue_type_slug', 'priority_slug', 'severity_slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0011_alter_issue_issue_type_alter_issue_priority_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='issue_type_slug',
            field=models.CharField(default='bug', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='issue',
            name='priority_slug',
            field=models.CharField(default='normal', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='issue',
            name='severity_slug',
            field=models.CharField(default='normal', max_length=20),
            preserve_default=False,
        ),
        migrations.RunPython(forwards, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='issue',
            name='issue_type',
        ),
        migrations.RemoveField(
            model_name='issue',
            name='priority',
        ),
        migrations.RemoveField(
            model_name='issue',
            name='severity',
        ),
        migrations.RenameField(
            model_name='issue',
            old_name='issue_type_slug',
            new_name='issue_type',
        ),
        migrations.RenameField(
            model_name='issue',
            old_name='priority_slug',
            new_name='priority',
        ),
        migrations.RenameField(
            model_name='issue',
            old_name='severity_slug',
            new_name='severity',
        ),
    ]
