import pandas as pd
from django.core.management.base import BaseCommand
from ionic_liquid.models import Anion_QC_data

class Command(BaseCommand):
    help = '从Excel/csv文件导入数据（先清空旧数据）'

    def handle(self, *args, **kwargs):
        
        Anion_QC_data.objects.all().delete()

        
        df = pd.read_excel('ionic_liquid/management/commands/HTQC_anion.xlsx')

        
        for _, row in df.iterrows():
            entry=Anion_QC_data(
                Name=row['Name'],
                SMILES=row['SMILES'],
                Anion_type=row['SMILES_type'],
                Energy_Hatree=row['Energy (Hatree)'],
                HOMO_Hatree=row['HOMO (Hatree)'],
                LUMO_Hatree=row['LUMO (Hatree)'],
                Thermal_correction_to_Enthalpy_Hatree=row['Thermal correction to Enthalpy (Hatree)'],
                Thermal_correction_to_Gibbs_Free_Energy_Hatree=row['Thermal correction to Gibbs Free Energy (Hatree)'],
                Entropy_J_per_mol_K=row['Entropy (J/mol·K)'],
                Dipole_Debye=row['Dipole (Debye)'],
                Gibbs_Free_Energy_Hatree=row['Gibbs Free Energy (Hatree)'],
                Enthalpy_Hatree=row['Enthalpy (Hatree)'],
                HOMO_LUMO_Gap_eV=row['HOMO LUMO Gap (eV)'],
            )
            
            entry.save()
        print('Excel/csv数据已成功导入到sqlite3数据库。')
