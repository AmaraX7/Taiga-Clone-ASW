from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.views.users import UserListView, UserDetailView
from api.views.issues import IssueListView

app_name = 'api'


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'user': request.user.username})


urlpatterns = [
    path('', health, name='health'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<str:username>/', UserDetailView.as_view(), name='user-detail'),
    path('issues/', IssueListView.as_view(), name='issue-list'),
    # Comments/Attachments/Watchers (Membre C), Catalogs (Membre D)
]
