from django.urls import path
from . import views

urlpatterns = [
    path('<str:username>/',      views.profile_view, name='profile_view'),
    path('<str:username>/edit/', views.profile_edit, name='profile_edit'),
]
