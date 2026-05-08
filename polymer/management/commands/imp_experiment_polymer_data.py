import pandas as pd
from django.core.management.base import BaseCommand
from polymer.models import experiment_polymer_data

class Command(BaseCommand):
    help = '从Excel/csv文件导入数据（先清空旧数据）'

    def handle(self, *args, **kwargs):
        
        experiment_polymer_data.objects.all().delete()

        
        df = pd.read_csv('polymer/saved_csv/final_polymer_properties_fromliterature.csv')

        
        for _, row in df.iterrows():
            entry=experiment_polymer_data(
                Name=row['Name'],
                PSMILES=row['PSMILES'],
                Bandgap_eV=row['Bandgap (eV)'],
                CO2_Permeability_Barrer=row['CO2 Permeability (Barrer)'],
                Compressive_Strength_MPa=row['Compressive Strength (MPa)'],
                Crystallization_Temperature_K=row['Crystallization Temperature (K)'],
                Elongation_at_Break_percentage=row['Elongation at Break (%)'],
                Flexural_Strength_MPa=row['Flexural Strength (MPa)'],
                Tg_K=row['Tg (K)'],
                H2_Permeability_Barrer=row['H2 Permeability (Barrer)'],
                Hardness_MPa=row['Hardness (MPa)'],
                Impact_Strength_kJ_per_m2=row['Impact Strength (kJ/m2)'],
                Ion_Exchange_Capacity_meq_per_g=row['Ion Exchange Capacity (meq/g)'],
                Limiting_Oxygen_Index_percentage=row['Limiting Oxygen Index (%)'],
                Lower_Critical_Solution_Temperature_K=row['Lower Critical Solution Temperature (K)'],
                Tm_K=row['Tm (K)'],
                Methanol_Permeability_cm2_per_s=row['Methanol Permeability (cm2/s)'],
                O2_Permeability_Barrer=row['O2 Permeability (Barrer)'],
                Refractive_Index=row['Refractive Index'],
                Swelling_Degree_percentage=row['Swelling Degree (%)'],
                Thermal_Conductivity_W_per_mK=row['Thermal Conductivity (W/m K)'],
                Tensile_Strength_MPa=row['Tensile Strength (MPa)'],
                Td_K=row['Td (K)'],
                Upper_Critical_Solution_Temperature_K=row['Upper Critical Solution Temperature (K)'],
                Water_Contact_Angle=row['Water Contact Angle'],
                Water_Uptake_percentage=row['Water Uptake (%)'],
                Youngs_Modulus_MPa=row['Youngs Modulus (MPa)'],
                Dielectric_Constant_Electronic=row['Dielectric Constant Electronic'],
                Dielectric_Constant_Ionic=row['Dielectric Constant Ionic'],
                Dielectric_Constant_Total=row['Dielectric Constant Total'],
                Density=row['Density (g/cm3)'],
                Reference=row['Reference'],
            )
            
            entry.save()
        print('Excel/csv数据已成功导入到sqlite3数据库。')
