from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

app_name = 'api'


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'user': request.user.username})


urlpatterns = [
    path('', health, name='health'),
    # Els endpoints s'afegiran aquí per cada membre:
    # Issues (Membre B), Comments/Attachments/Watchers (Membre C),
    # Catalogs (Membre D), Users (Membre E)
]
