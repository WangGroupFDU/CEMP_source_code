from django import forms
from .models import BMS_experiment_result

class BMS_result_form(forms.ModelForm):
    class Meta:
        
        model = BMS_experiment_result
        
        fields=["cathode","cathode_active_material","anode","li_metal_thickness","charge_rate","polymer",
                "polymer_percentage","intristic_viscosity","ionic_liquid","ionic_liquid_electrolyte","li_conc","temperature",
                "pressure","thickness","magnetic_field_direction","remark","bms_rawfile"]
class BatteryQueryForm(forms.Form):
    material = forms.CharField(required=False)
    temperature = forms.FloatField(required=False)
    percent = forms.IntegerField(required=False)
    size = forms.IntegerField(required=False)
    specific_capacity = forms.IntegerField(required=False)
    
    def clean(self):
        cleaned_data = super().clean()
        
        params = [k for k, v in cleaned_data.items() if v]
        if len(params) > 3:
            raise forms.ValidationError("最多只能选择三个查询条件")
        return cleaned_data
