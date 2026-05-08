import pandas as pd
from django.core.management.base import BaseCommand
from polymer.models import calculated_monomer_data

class Command(BaseCommand):
    help = '从Excel/csv文件导入数据（先清空旧数据）'

    def handle(self, *args, **kwargs):
        
        calculated_monomer_data.objects.all().delete()

        
        df = pd.read_csv('polymer/OMG_monomers_filter_qc_data.csv')

        
        for _, row in df.iterrows():
            entry=calculated_monomer_data(
                Name=row['Name'],
                SMILES=row['SMILES'],
                Neutral_Energy_Hatree=row['Neutral Energy (Hatree)'],
                Oxidation_Energy_Hatree=row['Oxidation Energy (Hatree)'],
                Reduction_Energy_Hatree=row['Reduction Energy (Hatree)'],
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
                Oxidation_Potential_V=row['Oxidation Potential (V)'],
                Reduction_Potential_V=row['Reduction Potential (V)'],
                Redox_Window_V=row['Redox Window (V)'],
                Monomer_Type=row['Monomer Type'],
                IP_Hatree=row['IP'],
                EA_Hatree=row['EA'],
                Mulliken_Electronegativity_Hatree=row['Mulliken Electronegativity'],
                Chemical_Potential_Hatree=row['Chemical Potential'],
                Hardness_Hatree=row['Hardness'],
                Softness_Hatree=row['Softness'],
                Electrophilicity_Index_Hatree=row['Electrophilicity Index'],
                Corrected_Redox_Window_V=row['Corrected Redox Window (V)'],
                Acetone_Gibbs_Free_Energy_Hatree=row['Acetone-Gibbs Free Energy (Hatree)'],
                Acetone_Solvation_Free_Energy_kJ_per_mol=row['Acetone Solvation Free Energy (kJ/mol)'],
                Chloroform_Gibbs_Free_Energy_Hatree=row['Chloroform-Gibbs Free Energy (Hatree)'],
                Chloroform_Solvation_Free_Energy_kJ_per_mol=row['Chloroform Solvation Free Energy (kJ/mol)'],
                DMF_Gibbs_Free_Energy_Hatree=row['DMF-Gibbs Free Energy (Hatree)'],
                DMF_Solvation_Free_Energy_kJ_per_mol=row['DMF Solvation Free Energy (kJ/mol)'],
                DMSO_Gibbs_Free_Energy_Hatree=row['DMSO-Gibbs Free Energy (Hatree)'],
                DMSO_Solvation_Free_Energy_kJ_per_mol=row['DMSO Solvation Free Energy (kJ/mol)'],
                Hexane_Gibbs_Free_Energy_Hatree=row['Hexane-Gibbs Free Energy (Hatree)'],
                Hexane_Solvation_Free_Energy_kJ_per_mol=row['Hexane Solvation Free Energy (kJ/mol)'],
                Water_Gibbs_Free_Energy_Hatree=row['Water-Gibbs Free Energy (Hatree)'],
                Water_Solvation_Free_Energy_kJ_per_mol=row['Water Solvation Free Energy (kJ/mol)'],
                THF_Gibbs_Free_Energy_Hatree=row['THF-Gibbs Free Energy (Hatree)'],
                THF_Solvation_Free_Energy_kJ_per_mol=row['THF Solvation Free Energy (kJ/mol)'],
            )
            
            entry.save()
        print('Excel/csv数据已成功导入到sqlite3数据库。')
