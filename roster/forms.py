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
        
    # roster/forms.py

class BatchLeaveForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Начална дата"
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Крайна дата"
    )
    leave_type = forms.ChoiceField(
        choices=[
            ('home', 'Домашен отпуск'),
            ('reward', 'Награда (Отпуск)'), # Използваме логиката на отпуска
            ('sick', 'Болничен'),
            ('mission', 'Командировка'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Вид"
    )
    reason = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Напр: За отлична служба'}),
        label="Причина / Бележка"
    )