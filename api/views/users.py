from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, JSONParser
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from accounts.models import UserProfile
from issues.models import Comment
from api.serializers.users import UserProfileSerializer
from api.serializers.issues import UserCommentSerializer


def _first_error(errors):
    for field, messages in errors.items():
        if isinstance(messages, list):
            return f"{field}: {messages[0]}"
        if isinstance(messages, dict):
            return _first_error(messages)
    return "Invalid data."


class UserListView(APIView):
    def get(self, request):
        profiles = UserProfile.objects.select_related('user').all()
        serializer = UserProfileSerializer(profiles, many=True, context={'request': request})
        return Response(serializer.data)


class UserDetailView(APIView):
    parser_classes = [MultiPartParser, JSONParser]

    def _get_profile(self, username):
        try:
            return User.objects.select_related('profile').get(username=username).profile
        except User.DoesNotExist:
            return None

    def get(self, request, username):
        profile = self._get_profile(username)
        if not profile:
            return Response(
                {'message': f"No user with username '{username}' found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UserProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)

    def put(self, request, username):
        if request.user.username != username:
            return Response(
                {'message': 'You do not have permission to perform this action.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        profile = self._get_profile(username)
        if not profile:
            return Response(
                {'message': f"No user with username '{username}' found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UserProfileSerializer(
            profile, data=request.data, partial=True, context={'request': request}
        )
        if not serializer.is_valid():
            return Response(
                {'message': _first_error(serializer.errors)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(serializer.data)


@api_view(['GET'])
def user_comments(request, username):
    user = get_object_or_404(User, username=username)
    comments = Comment.objects.filter(author=user).select_related('issue').order_by('-created_at')
    serializer = UserCommentSerializer(comments, many=True)
    return Response(serializer.data)
