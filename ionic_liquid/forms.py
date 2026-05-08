from django import forms
from .models import IL_properties


class IonicLiquidFilterForm(forms.Form):
    cation_type = forms.ModelChoiceField(queryset = IL_properties.objects.order_by('cation_type')
                                         .values_list('cation_type', flat=True).distinct())
    anion_type = forms.ModelChoiceField(queryset = IL_properties.objects.order_by('anion_type')
                                        .values_list('anion_type', flat=True).distinct())
    CHOICES = (
        ('physical', 'physical'),
    )
    dataset = forms.ChoiceField(choices = CHOICES)

class IonicLiquidNameForm(forms.Form):
    cation_name = forms.ModelChoiceField(queryset = IL_properties.objects.order_by('cation')
                                         .values_list('cation', flat=True).distinct())
    anion_name= forms.ModelChoiceField(queryset = IL_properties.objects.order_by('anion')
                                        .values_list('anion', flat=True).distinct())
    CHOICES = (
        ('physical', 'physical'),
        ('rdkit', 'rdkit'),
        ('psi4', 'psi4'),
    )
    dataset = forms.ChoiceField(choices = CHOICES)

class Psi4TheoryForm(forms.Form):
    CHOICES = (
        ('scf', 'scf'),
        ('b3lyp', 'b3lyp'),
        ('mp2', 'mp2'),
        ('m062x', 'm062x'),
        ('m06l', 'm06l'),
        ('hf', 'hf'),
    )
    theory = forms.ChoiceField(choices = CHOICES)

class Psi4BasisForm(forms.Form):
    CHOICES = (
        ('6-31g*', '6-31g*'),
        ('6-311g*', '6-311g*'),
        ('6-311pg*', '6-311pg*'),
        ('6-311pg**', '6-311pg**'),
        ('6-311ppg**', '6-311ppg**'),

    )
    basis_set = forms.ChoiceField(choices = CHOICES)

class Psi4MethodForm(forms.Form):
    CHOICES = (
        ('single-point', 'single-point'),
        ('optimize', 'optimize'),
    )
    method = forms.ChoiceField(choices = CHOICES)
