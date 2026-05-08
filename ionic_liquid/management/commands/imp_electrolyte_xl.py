import pandas as pd
from ...models import electrolyte
from django.core.management.base import BaseCommand
import pandas as pd


class Command(BaseCommand):
    help = 'Import data from Excel file'

    def handle(self, *args, **kwargs):
        df = pd.read_excel('electrolyte.xlsx', engine='openpyxl')
        
        for index, row in df.iterrows():
            entry = electrolyte(
                Component_Name_B=row["Component_Name_B"],
                Component_SMILES_B=row["Component_SMILES_B"],
                Component_B_Energy_Hatree=row["Component_B_Energy_Hatree"],
                Component_B_Thermal_correction_to_Gibbs_Free_Energy_Hatree=row["Component_B_Thermal_correction_to_Gibbs_Free_Energy_Hatree"],
                Component_B_Thermal_correction_to_Enthalpy_Hatree=row["Component_B_Thermal_correction_to_Enthalpy_Hatree"],
                Component_B_Entropy_J_per_mol_K=row["Component_B_Entropy_J_per_mol_K"],
                Component_B_HOMO_Hatree=row["Component_B_HOMO_Hatree"],
                Component_B_LUMO_Hatree=row["Component_B_LUMO_Hatree"],
                Component_B_Dipole_Debye=row["Component_B_Dipole_Debye"],
                Component_B_Gibbs_Free_Energy_Hatree=row["Component_B_Gibbs_Free_Energy_Hatree"],
                Component_B_Enthalpy_Hatree=row["Component_B_Enthalpy_Hatree"],
                Component_B_ECW_V=row["Component_B_ECW_V"],
            )
            
            entry.save()

        print('Excel数据已成功导入到sqlite3数据库。')