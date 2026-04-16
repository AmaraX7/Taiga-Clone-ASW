from django import forms
from django.contrib.auth.models import User
from .models import Issue


class IssueForm(forms.ModelForm):
    deadline = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Deadline',
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label='Unassigned',
        label='Assign to',
    )
    class Meta:
        model = Issue
        fields = ['subject', 'description', 'deadline', 'assigned_to']


class AssignIssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['assigned_to']

    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label='Unassigned',
    )


class AddWatcherForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=True,
        empty_label='Select user...',
    )


class AttachmentForm(forms.Form):
    file = forms.FileField()
