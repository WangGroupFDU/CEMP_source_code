


from rest_framework import serializers
from ionic_liquid.models import electrolyte
from ionic_liquid.models import metal_anion_energy
from ionic_liquid.models import IL,Cation,Anion
from ionic_liquid.models import Li_electrolyte

class ElectrolyteSerializer(serializers.ModelSerializer):
    class Meta:
        model = electrolyte
        fields = '__all__'  

class Metal_Anion_EnergySerializer(serializers.ModelSerializer):
    class Meta:
        model = metal_anion_energy
        fields = '__all__'  
        
class ILSerializer(serializers.ModelSerializer):
    class Meta:
        model = IL
        fields = '__all__'  

class CationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cation
        fields = '__all__'  

class Li_ElectrolyteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Li_electrolyte
        fields = '__all__'  

class AnionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anion
        fields = '__all__'  