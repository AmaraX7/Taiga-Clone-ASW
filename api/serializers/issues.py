from rest_framework import serializers
from django.contrib.auth.models import User
from issues.models import Issue, IssueActivity, IssueStatus, IssueTag, Watcher


class IssueStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueStatus
        fields = ['id', 'name', 'slug', 'color', 'is_closed']


class IssueUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']


class IssueTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueTag
        fields = ['name', 'slug', 'color']


class IssueListSerializer(serializers.ModelSerializer):
    status = IssueStatusSerializer(read_only=True)
    assigned_to = IssueUserSerializer(read_only=True)
    created_by = IssueUserSerializer(read_only=True)
    tags = IssueTagSerializer(many=True, read_only=True)
    deadline_status = serializers.ReadOnlyField()

    class Meta:
        model = Issue
        fields = [
            'id', 'subject', 'status', 'issue_type', 'severity', 'priority',
            'tags', 'deadline', 'deadline_status',
            'assigned_to', 'created_by', 'created_at', 'modified_at',
        ]


class IssueDetailSerializer(serializers.ModelSerializer):
    status = IssueStatusSerializer(read_only=True)
    assigned_to = IssueUserSerializer(read_only=True)
    created_by = IssueUserSerializer(read_only=True)
    tags = IssueTagSerializer(many=True, read_only=True)
    deadline_status = serializers.ReadOnlyField()

    class Meta:
        model = Issue
        fields = [
            'id', 'subject', 'description', 'status', 'issue_type', 'severity', 'priority',
            'tags', 'deadline', 'deadline_status',
            'assigned_to', 'created_by', 'created_at', 'modified_at',
        ]


class WatcherSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Watcher
        fields = ['user_id', 'username', 'created_at']


class IssueStatusUpdateSerializer(serializers.Serializer):
    status_id = serializers.IntegerField()

    def validate_status_id(self, value):
        try:
            return IssueStatus.objects.get(pk=value)
        except IssueStatus.DoesNotExist:
            raise serializers.ValidationError({"status_id": "Status not found."})
        
class IssueActivitySerializer(serializers.ModelSerializer):
    actor = IssueUserSerializer(read_only=True)

    class Meta:
        model = IssueActivity
        fields = ['id', 'actor', 'action', 'details', 'created_at']