from rest_framework import serializers

from issues.models import (
    DueDatePreset,
    IssuePriority,
    IssueSeverity,
    IssueStatus,
    IssueTag,
    IssueType,
)


class IssueStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueStatus
        fields = ['id', 'name', 'slug', 'color', 'is_closed', 'order']


class IssueTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueType
        fields = ['id', 'name', 'slug', 'color', 'order']


class IssueSeveritySerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueSeverity
        fields = ['id', 'name', 'slug', 'color', 'order']


class IssuePrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = IssuePriority
        fields = ['id', 'name', 'slug', 'color', 'order']


class IssueTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueTag
        fields = ['id', 'name', 'slug', 'color']


class DueDatePresetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DueDatePreset
        fields = ['id', 'name', 'days_from_today', 'order']
