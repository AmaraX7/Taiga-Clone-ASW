from django import forms
from .models import Issue


class IssueForm(forms.ModelForm):
    deadline = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Deadline',
    )

    class Meta:
        model = Issue
        fields = ['subject', 'description', 'deadline']