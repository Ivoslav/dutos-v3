from django import forms
from .models import DutyShift

class DutyShiftForm(forms.ModelForm):
    class Meta:
        model = DutyShift
        fields = ['date', 'duty_type']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'duty_type': forms.Select(attrs={'class': 'form-select'}),
        }