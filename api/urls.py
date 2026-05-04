from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.views.users import UserListView, UserDetailView

app_name = 'api'


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'user': request.user.username})


urlpatterns = [
    path('', health, name='health'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<str:username>/', UserDetailView.as_view(), name='user-detail'),
    # Issues (Membre B), Comments/Attachments/Watchers (Membre C),
    # Catalogs (Membre D)
]
