import pandas as pd
from ...models import metal_anion_energy
from django.core.management.base import BaseCommand
import pandas as pd


class Command(BaseCommand):
    help = 'Import data from Excel file'

    def handle(self, *args, **kwargs):
        df = pd.read_excel('Dimer.xlsx', engine='openpyxl')
        
        for index, row in df.iterrows():
            
            entry = metal_anion_energy(
                Dimer_Name=row['Dimer Name'],
                Dimer_SMILES=row['Dimer SMILES'],
                Component_Name_A=row['Component Name A'],
                Component_SMILES_A=row['Component SMILES A'],
                Component_Name_B=row['Component Name B'],
                Component_SMILES_B=row['Component SMILES B'],
                Component_A_Energy_Hatree=row['Component A Energy (Hatree)'],
                Component_B_Energy_Hatree=row['Component B Energy (Hatree)'],
                Component_A_Thermal_correction_to_Gibbs_Free_Energy_Hatree=row['Component A Thermal correction to Gibbs Free Energy (Hatree)'],
                Component_B_Thermal_correction_to_Gibbs_Free_Energy_Hatree=row['Component B Thermal correction to Gibbs Free Energy (Hatree)'],
                Component_A_Thermal_correction_to_Enthalpy_Hatree=row['Component A Thermal correction to Enthalpy (Hatree)'],
                Component_B_Thermal_correction_to_Enthalpy_Hatree=row['Component B Thermal correction to Enthalpy (Hatree)'],
                Component_A_Entropy_J_mol_K=row['Component A Entropy (J/mol·K)'],
                Component_B_Entropy_J_mol_K=row['Component B Entropy (J/mol·K)'],
                Component_A_HOMO_Hatree=row['Component A HOMO (Hatree)'],
                Component_B_HOMO_Hatree=row['Component B HOMO (Hatree)'],
                Component_A_Dipole_Debye=row['Component A Dipole (Debye)'],
                Component_B_Dipole_Debye=row['Component B Dipole (Debye)'],
                Component_A_LUMO_Hatree=row['Component A LUMO (Hatree)'],
                Component_B_LUMO_Hatree=row['Component B LUMO (Hatree)'],
                Component_A_Gibbs_Free_Energy_Hatree=row['Component A Gibbs Free Energy (Hatree)'],
                Component_A_Enthalpy_Hatree=row['Component A Enthalpy (Hatree)'],
                Component_B_Gibbs_Free_Energy_Hatree=row['Component B Gibbs Free Energy (Hatree)'],
                Component_B_Enthalpy_Hatree=row['Component B Enthalpy (Hatree)'],
                Dimer_Energy_Hatree=row['Dimer Energy (Hatree)'],
                Dimer_Thermal_correction_to_Gibbs_Free_Energy_Hatree=row['Dimer Thermal correction to Gibbs Free Energy (Hatree)'],
                Dimer_Thermal_correction_to_Enthalpy_Hatree=row['Dimer Thermal correction to Enthalpy (Hatree)'],
                Dimer_Entropy_J_mol_K=row['Dimer Entropy (J/mol·K)'],
                Dimer_HOMO_Hatree=row['Dimer HOMO (Hatree)'],
                Dimer_Dipole_Debye=row['Dimer Dipole (Debye)'],
                Dimer_LUMO_Hatree=row['Dimer LUMO (Hatree)'],
                Dimer_Gibbs_Free_Energy_Hatree=row['Dimer Gibbs Free Energy (Hatree)'],
                Dimer_Enthalpy_Hatree=row['Dimer Enthalpy (Hatree)'],
                Binding_energy_kJ_mol=row['Binding energy (kJ/mol)']
            )
            
            entry.save()

        print('Excel数据已成功导入到数据库。')
