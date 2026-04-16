from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0004_comment_modified_at_issue_modified_at_watcher'),
    ]

    operations = [
        migrations.CreateModel(
            name='IssueStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('color', models.CharField(default='#70728f', help_text='Hex colour, e.g. #4c9aff', max_length=7)),
                ('is_closed', models.BooleanField(default=False, help_text='Issues with this status count as closed')),
                ('order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'ordering': ['order', 'name'],
            },
        ),
    ]
