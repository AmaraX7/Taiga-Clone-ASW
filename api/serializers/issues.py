from rest_framework import serializers
from django.contrib.auth.models import User
from issues.models import Comment, Issue, IssueActivity, IssueStatus, IssueTag, Watcher, Attachment, IssueType, IssueSeverity, IssuePriority


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


class IssueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueType
        fields = ['name', 'slug', 'color']


class IssueSeveritySerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueSeverity
        fields = ['name', 'slug', 'color']


class IssuePrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = IssuePriority
        fields = ['name', 'slug', 'color']


def _resolve_type(slug, context):
    t = context.get('type_map', {}).get(slug)
    return IssueTypeSerializer(t).data if t else {'name': slug, 'slug': slug, 'color': '#6b7280'}


def _resolve_severity(slug, context):
    s = context.get('severity_map', {}).get(slug)
    return IssueSeveritySerializer(s).data if s else {'name': slug, 'slug': slug, 'color': '#6b7280'}


def _resolve_priority(slug, context):
    p = context.get('priority_map', {}).get(slug)
    return IssuePrioritySerializer(p).data if p else {'name': slug, 'slug': slug, 'color': '#6b7280'}


class IssueListSerializer(serializers.ModelSerializer):
    status = IssueStatusSerializer(read_only=True)
    assigned_to = IssueUserSerializer(read_only=True)
    created_by = IssueUserSerializer(read_only=True)
    tags = IssueTagSerializer(many=True, read_only=True)
    deadline_status = serializers.ReadOnlyField()
    issue_type = serializers.SerializerMethodField()
    severity = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()

    def get_issue_type(self, obj):
        return _resolve_type(obj.issue_type, self.context)

    def get_severity(self, obj):
        return _resolve_severity(obj.severity, self.context)

    def get_priority(self, obj):
        return _resolve_priority(obj.priority, self.context)

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
    status_id = serializers.PrimaryKeyRelatedField(
        queryset=IssueStatus.objects.all(),
        source='status',
        write_only=True,
        required=False,
    )
    issue_type = serializers.SerializerMethodField()
    severity = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    issue_type_slug = serializers.CharField(source='issue_type', write_only=True, required=False)
    severity_slug = serializers.CharField(source='severity', write_only=True, required=False)
    priority_slug = serializers.CharField(source='priority', write_only=True, required=False)

    def get_issue_type(self, obj):
        return _resolve_type(obj.issue_type, self.context)

    def get_severity(self, obj):
        return _resolve_severity(obj.severity, self.context)

    def get_priority(self, obj):
        return _resolve_priority(obj.priority, self.context)

    class Meta:
        model = Issue
        fields = [
            'id', 'status_id', 'subject', 'description', 'status',
            'issue_type', 'issue_type_slug', 'severity', 'severity_slug',
            'priority', 'priority_slug',
            'tags', 'deadline', 'deadline_status',
            'assigned_to', 'created_by', 'created_at', 'modified_at',
        ]


class WatcherSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Watcher
        fields = ['username', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    issue_id = serializers.IntegerField(source='issue.id', read_only=True)
    author = IssueUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'issue_id', 'author', 'text', 'created_at', 'modified_at']
        read_only_fields = ['id', 'issue_id', 'author', 'created_at', 'modified_at']


class UserCommentSerializer(serializers.ModelSerializer):
    issue_id = serializers.IntegerField(source='issue.id', read_only=True)
    issue_subject = serializers.CharField(source='issue.subject', read_only=True)
    author = IssueUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'issue_id', 'issue_subject', 'author', 'text', 'created_at', 'modified_at']


class IssueBulkInsertSerializer(serializers.Serializer):
    issues_text = serializers.CharField()
    status_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_issues_text(self, value):
        if not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def validate_status_id(self, value):
        if value is None:
            return None
        try:
            return IssueStatus.objects.get(pk=value)
        except IssueStatus.DoesNotExist:
            raise serializers.ValidationError("Status not found.")


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

class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.CharField(source='uploaded_by.username', read_only=True)
    issue_id = serializers.IntegerField(source='issue.id', read_only=True)

    class Meta:
        model = Attachment
        fields = ['id', 'issue_id', 'uploaded_by', 'file', 'created_at']
        read_only_fields = ['id', 'issue_id', 'uploaded_by', 'created_at']
class AttachmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['file']
