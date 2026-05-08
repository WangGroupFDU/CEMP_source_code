from django import forms

class CrystalForm(forms.Form):
    ionic_liquid_name = forms.CharField(label='ionic_liquid_name', max_length=100)