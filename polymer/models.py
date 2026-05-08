
from django.db import models


class polymer_properties(models.Model):
    label = models.CharField(max_length=200)
    formula = models.CharField(max_length=200)
    cation = models.CharField(max_length=200)
    anion = models.CharField(max_length=200)
    cation_type = models.CharField(max_length=200)
    anion_type = models.CharField(max_length=200)
    ECW = models.FloatField(default = None)
    melting_point = models.CharField(max_length=200,default = None)
    conductivity = models.FloatField(default = None)
    viscosity = models.CharField(max_length=200,default = None)
    density = models.FloatField(default = None)
    T_conductivity = models.IntegerField(default = None)
    T_viscosity = models.IntegerField(default = None)
    T_density = models.IntegerField(default = None)
    conductivity_norm = models.FloatField(default = None)
    viscosity_norm = models.FloatField(default = None)
    density_norm = models.FloatField(default = None)
    


class polymer_smiles_psi4(models.Model):
    
    name = models.CharField(max_length=200)
    smile_form = models.CharField(max_length=200)
    energy = models.FloatField()
    HOMO = models.FloatField()
    LUMO = models.FloatField()
    dipole_x = models.FloatField()
    dipole_y = models.FloatField()
    dipole_z = models.FloatField()
    dipole_total = models.FloatField()
    type = models.CharField(max_length=200)
    

class polymer_smiles_rdkit(models.Model):
    
    name = models.CharField(max_length=200)
    smile_form = models.CharField(max_length=200)
    Asphericity = models.FloatField()
    Eccentricity = models.FloatField()
    NPR1 = models.FloatField()
    NPR2 = models.FloatField()
    PMI1 = models.FloatField()
    PMI2 = models.FloatField()
    PMI3 = models.FloatField()
    RadiusOfGyration = models.FloatField()
    SpherocityIndex = models.FloatField()
    ExactMolWt = models.FloatField()
    FpDensityMorgan1 = models.FloatField()
    FpDensityMorgan2 = models.FloatField()
    HeavyAtomMolWt = models.FloatField()
    MaxAbsPartialCharge = models.FloatField()
    MaxPartialCharge = models.FloatField()
    MinPartialCharge = models.FloatField()
    NumRadicalElectrons = models.FloatField()
    NumValenceElectrons = models.FloatField()
    volume = models.FloatField()
    type = models.CharField(max_length=200)
    
class polyelectrolyte(models.Model):
    polyelectrolyte = models.CharField(max_length=255)
    copolymer = models.CharField(max_length=255)
    cation = models.CharField(max_length=255)
    anion = models.CharField(max_length=255)
    repeat_unit = models.CharField(max_length=255)
    dielectric_constant = models.CharField(max_length=255)
    chemical_structure = models.CharField(max_length=255)
    hydrophilic_hydrophobic = models.CharField(max_length=255)
    functional_group = models.CharField(max_length=255)
    application_function = models.CharField(max_length=255)
    reference = models.CharField(max_length=255)
    synonyms = models.CharField(max_length=255)
    chemdraw_file = models.CharField(max_length=255)
    
class experiment_polymer_data(models.Model):
    Name = models.CharField(max_length=255)  
    PSMILES = models.CharField(max_length=255)  
    Atomization_Energy_eV = models.FloatField(null=True, blank=True)   
    Bandgap_eV = models.FloatField(null=True, blank=True)  
    Bandgap_Bulk_eV = models.FloatField(null=True, blank=True)   
    Bandgap_Chain_eV = models.FloatField(null=True, blank=True)   
    CH4_Permeability_Barrer = models.FloatField(null=True, blank=True)   
    CO2_Permeability_Barrer = models.FloatField(null=True, blank=True)  
    Compressive_Strength_MPa = models.FloatField(null=True, blank=True)  
    Crystallization_Temperature_K = models.FloatField(null=True, blank=True)  
    Crystallization_Tendency_percentage = models.FloatField(null=True, blank=True)   
    Dielectric_Constant_Electronic = models.FloatField(null=True, blank=True)  
    Dielectric_Constant_Ionic = models.FloatField(null=True, blank=True)  
    Dielectric_Constant_Total = models.FloatField(null=True, blank=True)  
    Density = models.FloatField(null=True, blank=True)  
    Electron_Affinity_eV = models.FloatField(null=True, blank=True)   
    Elongation_at_Break_percentage = models.FloatField(null=True, blank=True)  
    Flexural_Strength_MPa = models.FloatField(null=True, blank=True)  
    Tg_K = models.FloatField(null=True, blank=True)  
    H2_Permeability_Barrer = models.FloatField(null=True, blank=True)  
    Hardness_MPa = models.FloatField(null=True, blank=True)  
    He_Permeability_Barrer = models.FloatField(null=True, blank=True)   
    Impact_Strength_kJ_per_m2 = models.FloatField(null=True, blank=True)  
    Ion_Exchange_Capacity_meq_per_g = models.FloatField(null=True, blank=True)  
    Ionization_Energy_eV = models.FloatField(null=True, blank=True)   
    Limiting_Oxygen_Index_percentage = models.FloatField(null=True, blank=True)  
    Lower_Critical_Solution_Temperature_K = models.FloatField(null=True, blank=True)  
    Tm_K = models.FloatField(null=True, blank=True)  
    Methanol_Permeability_cm2_per_s = models.FloatField(null=True, blank=True)  
    N2_Permeability_Barrer = models.FloatField(null=True, blank=True)   
    O2_Permeability_Barrer = models.FloatField(null=True, blank=True)  
    Refractive_Index = models.FloatField(null=True, blank=True)  
    Swelling_Degree_percentage = models.FloatField(null=True, blank=True)  
    Thermal_Conductivity_W_per_mK = models.FloatField(null=True, blank=True)  
    Tensile_Strength_MPa = models.FloatField(null=True, blank=True)  
    Td_K = models.FloatField(null=True, blank=True)  
    Upper_Critical_Solution_Temperature_K = models.FloatField(null=True, blank=True)  
    Water_Contact_Angle = models.FloatField(null=True, blank=True)  
    Water_Uptake_percentage = models.FloatField(null=True, blank=True)  
    Youngs_Modulus_MPa = models.FloatField(null=True, blank=True)  
    Reference = models.CharField(max_length=255, null=True, blank=True)  


class calculated_monomer_data(models.Model):
    
    Name = models.CharField(max_length=255)
    SMILES = models.CharField(max_length=255)
    Monomer_Type = models.CharField(max_length=255)
    Neutral_Energy_Hatree = models.FloatField(null=True,blank=True)
    Oxidation_Energy_Hatree = models.FloatField(null=True,blank=True)
    Reduction_Energy_Hatree = models.FloatField(null=True,blank=True)
    HOMO_eV = models.FloatField(null=True,blank=True)
    LUMO_eV = models.FloatField(null=True,blank=True)
    Inner_energy_correction_Hatree = models.FloatField(null=True,blank=True)
    Thermal_correction_to_Enthalpy_Hatree = models.FloatField(null=True,blank=True)
    Thermal_correction_to_Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    Entropy_Hatree = models.FloatField(null=True,blank=True)
    Dipole_Debye = models.FloatField(null=True,blank=True)
    Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    Enthalpy_Hatree = models.FloatField(null=True,blank=True)
    HOMO_LUMO_Gap_eV = models.FloatField(null=True,blank=True)
    Oxidation_Potential_V = models.FloatField(null=True,blank=True)
    Reduction_Potential_V = models.FloatField(null=True,blank=True)
    Redox_Window_V = models.FloatField(null=True,blank=True)
    IP_Hatree = models.FloatField(null=True,blank=True)
    EA_Hatree = models.FloatField(null=True,blank=True)
    Mulliken_Electronegativity_Hatree = models.FloatField(null=True,blank=True)
    Chemical_Potential_Hatree = models.FloatField(null=True,blank=True)
    Hardness_Hatree = models.FloatField(null=True,blank=True)
    Softness_Hatree = models.FloatField(null=True,blank=True)
    Electrophilicity_Index_Hatree = models.FloatField(null=True,blank=True)
    Corrected_Redox_Window_V = models.FloatField(null=True,blank=True)
    Acetone_Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    Acetone_Solvation_Free_Energy_kJ_per_mol = models.FloatField(null=True,blank=True)
    Chloroform_Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    Chloroform_Solvation_Free_Energy_kJ_per_mol = models.FloatField(null=True,blank=True)
    DMF_Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    DMF_Solvation_Free_Energy_kJ_per_mol = models.FloatField(null=True,blank=True)
    DMSO_Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    DMSO_Solvation_Free_Energy_kJ_per_mol = models.FloatField(null=True,blank=True)
    Hexane_Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    Hexane_Solvation_Free_Energy_kJ_per_mol = models.FloatField(null=True,blank=True)
    Water_Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    Water_Solvation_Free_Energy_kJ_per_mol = models.FloatField(null=True,blank=True)
    THF_Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    THF_Solvation_Free_Energy_kJ_per_mol = models.FloatField(null=True,blank=True)
    Software = models.CharField(
        max_length=255,
        default='ORCA',
        help_text='Calculation Software'
    )
    Theory_Level = models.CharField(
        max_length=255,
        default='opt+freq: b3lyp/def2-TZVP em=gd3bj\nenergy: wB97M-V/ma-def2-TZVP',
        help_text='Calcualtion Theory Level'
    )
    Source = models.CharField(
        max_length=255,
        default='QC',
        help_text='From Quantum Chemistry Calculation'
    )
    
class calculated_polymer_data(models.Model):
    
    Name = models.CharField(max_length=255)
    reactant_1 = models.CharField(max_length=255)
    reactant_2 = models.CharField(max_length=255)
    psmiles = models.CharField(max_length=255)
    SMILES = models.CharField(max_length=255)
    reaction_type = models.CharField(max_length=255)
    Energy_Hatree = models.FloatField(null=True,blank=True)
    es = models.FloatField(null=True,blank=True)
    Isotropic_Polarizability_au = models.FloatField(null=True,blank=True)
    HOMO_eV = models.FloatField(null=True,blank=True)
    LUMO_eV = models.FloatField(null=True,blank=True)
    Inner_energy_correction_Hatree = models.FloatField(null=True,blank=True)
    Thermal_correction_to_Enthalpy_Hatree = models.FloatField(null=True,blank=True)
    Thermal_correction_to_Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    Entropy_Hatree = models.FloatField(null=True,blank=True)
    Dipole_Debye = models.FloatField(null=True,blank=True)
    Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    Enthalpy_Hatree = models.FloatField(null=True,blank=True)
    HOMO_LUMO_Gap_eV = models.FloatField(null=True,blank=True)
    Software = models.CharField(
        max_length=255,
        default='ORCA',
        help_text='Calculation Software'
    )
    Theory_Level = models.CharField(
        max_length=255,
        default='opt+freq: b3lyp/def2-TZVP em=gd3bj\nenergy: wB97M-V/ma-def2-TZVP',
        help_text='Calcualtion Theory Level'
    )
    Source = models.CharField(
        max_length=255,
        default='QC',
        help_text='From Quantum Chemistry Calculation'
    )
