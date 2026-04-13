from django import forms
from .models import UserProfile


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model  = UserProfile
        fields = ['bio', 'avatar']
        widgets = {
            'bio':    forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell something about yourself…'}),
            'avatar': forms.FileInput(attrs={'class': 'avatar-file-input', 'accept': 'image/*'}),
        }
