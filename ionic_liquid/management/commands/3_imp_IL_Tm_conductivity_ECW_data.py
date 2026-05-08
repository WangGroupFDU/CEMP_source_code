import pandas as pd
from django.core.management.base import BaseCommand
from ionic_liquid.models import IL_Tm_conductivity_ECW_data

class Command(BaseCommand):
    help = '从Excel/csv文件导入数据（先清空旧数据）'

    def handle(self, *args, **kwargs):
        
        IL_Tm_conductivity_ECW_data.objects.all().delete()

        
        df = pd.read_excel('ionic_liquid/management/commands/Ionic_liquid_Tm_conductivity_ECW.xlsx')

        
        for _, row in df.iterrows():
            entry=IL_Tm_conductivity_ECW_data(
                Name=row['Name'],
                SMILES=row['SMILES'],
                Anion_SMILES=row['Anion_SMILES'],
                Cation_SMILES=row['Cation_SMILES'],
                Cation_SMILES_type=row['Cation_SMILES_type'],
                Anion_SMILES_type=row['Anion_SMILES_type'],
                Conductivity_mS_per_cm=row['Conductivity (mS/cm)'],
                Tm_K=row['Tm (K)'],
                ECW_V=row['ECW (V)'],
                Type=row['Type'],

            )
            
            entry.save()
        print('Excel/csv数据已成功导入到sqlite3数据库。')
