from django import forms

class PolymerForm(forms.Form):
    ionic_liquid_name = forms.CharField(label='ionic_liquid_name', max_length=100)