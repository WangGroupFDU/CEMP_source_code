import pandas as pd
from ...models import IL
from django.core.management.base import BaseCommand
import pandas as pd


class Command(BaseCommand):
    help = 'Import data from Excel file'

    def handle(self, *args, **kwargs):
        df = pd.read_excel('IL.xlsx', engine='openpyxl')
        
        for index, row in df.iterrows():
            entry = IL(
                Name=row["Name"],
                SMILES=row["SMILES"],
                Energy_Hatree=row["Energy_Hatree"],
                Thermal_correction_to_Gibbs_Free_Energy_Hatree=row["Thermal_correction_to_Gibbs_Free_Energy_Hatree"],
                Thermal_correction_to_Enthalpy_Hatree=row["Thermal_correction_to_Enthalpy_Hatree"],
                Entropy_J_per_mol_K=row["Entropy_J_per_mol_K"],
                HOMO_Hatree=row["HOMO_Hatree"],
                LUMO_Hatree=row["LUMO_Hatree"],
                Dipole_Debye=row["Dipole_Debye"],
                Gibbs_Free_Energy_Hatree=row["Gibbs_Free_Energy_Hatree"],
                Enthalpy_Hatree=row["Enthalpy_Hatree"],
                ECW_V=row["ECW_V"],
            )
            
            entry.save()

        print('Excel数据已成功导入到sqlite3数据库。')
