from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0012_revert_issue_catalog_fields_to_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issue',
            name='issue_type',
            field=models.CharField(default='bug', max_length=20),
        ),
        migrations.AlterField(
            model_name='issue',
            name='priority',
            field=models.CharField(default='normal', max_length=10),
        ),
        migrations.AlterField(
            model_name='issue',
            name='severity',
            field=models.CharField(default='normal', max_length=20),
        ),
    ]
