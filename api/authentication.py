from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from accounts.models import UserProfile


class ApiKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        raw = request.headers.get('Authorization', '')
        if not raw.startswith('Api-Key '):
            return None
        api_key = raw[len('Api-Key '):]
        try:
            profile = UserProfile.objects.select_related('user').get(api_key=api_key)
        except UserProfile.DoesNotExist:
            raise AuthenticationFailed('Invalid API key.')
        return (profile.user, None)

    def authenticate_header(self, request):
        return 'ApiKey'
