from django import forms

from . import models


class ChangeTitleForm(forms.ModelForm):
    class Meta:
        model = models.Article
        fields = ('title',)
