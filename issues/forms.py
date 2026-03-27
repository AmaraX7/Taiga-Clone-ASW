from django import forms
from django.contrib.auth.models import User
from .models import Issue


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['subject', 'description']


class AssignIssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['assigned_to']

    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label='Unassigned',
    )


class AttachmentForm(forms.Form):
    file = forms.FileField()
