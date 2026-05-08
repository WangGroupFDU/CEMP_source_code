import pandas as pd
from ...models import Li_electrolyte
from django.core.management.base import BaseCommand
import pandas as pd


class Command(BaseCommand):
    help = 'Import data from Excel file'

    def handle(self, *args, **kwargs):
        df = pd.read_excel('Li+-electrolyte.xlsx', engine='openpyxl')
        
        for index, row in df.iterrows():
            entry = Li_electrolyte(
                Dimer_Name=row["Dimer_Name"],
                Dimer_SMILES=row["Dimer_SMILES"],
                Component_Name_A=row["Component_Name_A"],
                Component_SMILES_A=row["Component_SMILES_A"],
                Component_Name_B=row["Component_Name_B"],
                Component_SMILES_B=row["Component_SMILES_B"],
                Component_A_Energy_Hatree=row["Component_A_Energy_Hatree"],
                Component_B_Energy_Hatree=row["Component_B_Energy_Hatree"],
                Component_B_Thermal_correction_to_Gibbs_Free_Energy_Hatree=row["Component_B_Thermal_correction_to_Gibbs_Free_Energy_Hatree"],
                Component_B_Thermal_correction_to_Enthalpy_Hatree=row["Component_B_Thermal_correction_to_Enthalpy_Hatree"],
                Component_B_Entropy_J_per_mol_K=row["Component_B_Entropy_J_per_mol_K"],
                Component_A_HOMO_Hatree=row["Component_A_HOMO_Hatree"],
                Component_B_HOMO_Hatree=row["Component_B_HOMO_Hatree"],
                Component_A_Dipole_Debye=row["Component_A_Dipole_Debye"],
                Component_B_Dipole_Debye=row["Component_B_Dipole_Debye"],
                Component_A_LUMO_Hatree=row["Component_A_LUMO_Hatree"],
                Component_B_LUMO_Hatree=row["Component_B_LUMO_Hatree"],
                Component_B_Gibbs_Free_Energy_Hatree=row["Component_B_Gibbs_Free_Energy_Hatree"],
                Component_B_Enthalpy_Hatree=row["Component_B_Enthalpy_Hatree"],
                Dimer_Energy_Hatree=row["Dimer_Energy_Hatree"],
                Dimer_Thermal_correction_to_Gibbs_Free_Energy_Hatree=row["Dimer_Thermal_correction_to_Gibbs_Free_Energy_Hatree"],
                Dimer_Thermal_correction_to_Enthalpy_Hatree=row["Dimer_Thermal_correction_to_Enthalpy_Hatree"],
                Dimer_Entropy_J_per_mol_K=row["Dimer_Entropy_J_per_mol_K"],
                Dimer_HOMO_Hatree=row["Dimer_HOMO_Hatree"],
                Dimer_LUMO_Hatree=row["Dimer_LUMO_Hatree"],
                Dimer_Dipole_Debye=row["Dimer_Dipole_Debye"],
                Dimer_Gibbs_Free_Energy_Hatree=row["Dimer_Gibbs_Free_Energy_Hatree"],
                Dimer_Enthalpy_Hatree=row["Dimer_Enthalpy_Hatree"],
                Binding_energy_kJ_per_mol=row["Binding_energy_kJ_per_mol"],
            )
            
            entry.save()

        print('Excel数据已成功导入到sqlite3数据库。')