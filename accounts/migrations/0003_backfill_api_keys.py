import secrets
from django.db import migrations


def generate_api_keys(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    for profile in UserProfile.objects.filter(api_key__isnull=True):
        profile.api_key = secrets.token_hex(32)
        profile.save(update_fields=['api_key'])


class Migration(migrations.Migration):
    dependencies = [('accounts', '0002_userprofile_api_key')]
    operations = [
        migrations.RunPython(generate_api_keys, migrations.RunPython.noop),
    ]
