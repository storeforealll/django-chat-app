from django import forms
from .models import Profile,Story

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'bio']


class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ['title', 'content', 'media']
