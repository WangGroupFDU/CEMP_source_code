import pandas as pd
from django.core.management.base import BaseCommand
from polymer.models import calculated_polymer_data

class Command(BaseCommand):
    help = '从Excel/csv文件导入数据（先清空旧数据）'

    def handle(self, *args, **kwargs):
        
        calculated_polymer_data.objects.all().delete()

        
        df = pd.read_excel('polymer/polyerm_qcdata_part1.xlsx')

        
        for _, row in df.iterrows():
            entry=calculated_polymer_data(
                Name=row['Name'],
                SMILES=row['SMILES'],
                reactant_1=row['reactant_1'],
                reactant_2=row['reactant_2'],
                psmiles=row['smiles'],
                reaction_type=row['reaction_type'],
                es=row['es'],
                Energy_Hatree=row['Energy (Hatree)'],
                Isotropic_Polarizability_au=row['Isotropic Polarizability (a.u.)'],
                HOMO_eV=row['HOMO (eV)'],
                LUMO_eV=row['LUMO (eV)'],
                Inner_energy_correction_Hatree=row['Inner energy correction (Hatree)'],
                Thermal_correction_to_Enthalpy_Hatree=row['Thermal correction to Enthalpy (Hatree)'],
                Thermal_correction_to_Gibbs_Free_Energy_Hatree=row['Thermal correction to Gibbs Free Energy (Hatree)'],
                Entropy_Hatree=row['Entropy (Hatree)'],
                Dipole_Debye=row['Dipole (Debye)'],
                Gibbs_Free_Energy_Hatree=row['Gibbs Free Energy (Hatree)'],
                Enthalpy_Hatree=row['Enthalpy (Hatree)'],
                HOMO_LUMO_Gap_eV=row['HOMO LUMO Gap (eV)'],
            )
            
            entry.save()
        print('Excel/csv数据已成功导入到sqlite3数据库。')
