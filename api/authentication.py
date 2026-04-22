from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from accounts.models import UserProfile


class ApiKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get('Authorization')
        if not api_key:
            return None
        try:
            profile = UserProfile.objects.select_related('user').get(api_key=api_key)
        except UserProfile.DoesNotExist:
            raise AuthenticationFailed('Invalid API key.')
        return (profile.user, None)

    def authenticate_header(self, request):
        return 'ApiKey'
