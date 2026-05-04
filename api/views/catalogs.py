from rest_framework import viewsets

from issues.models import IssuePriority, IssueSeverity, IssueStatus, IssueTag, IssueType

from api.serializers.catalogs import (
    IssuePrioritySerializer,
    IssueSeveritySerializer,
    IssueStatusSerializer,
    IssueTagSerializer,
    IssueTypeSerializer,
)


class IssueStatusViewSet(viewsets.ModelViewSet):
    queryset = IssueStatus.objects.all()
    serializer_class = IssueStatusSerializer


class IssueTypeViewSet(viewsets.ModelViewSet):
    queryset = IssueType.objects.all()
    serializer_class = IssueTypeSerializer


class IssueSeverityViewSet(viewsets.ModelViewSet):
    queryset = IssueSeverity.objects.all()
    serializer_class = IssueSeveritySerializer


class IssuePriorityViewSet(viewsets.ModelViewSet):
    queryset = IssuePriority.objects.all()
    serializer_class = IssuePrioritySerializer


class IssueTagViewSet(viewsets.ModelViewSet):
    queryset = IssueTag.objects.all()
    serializer_class = IssueTagSerializer
