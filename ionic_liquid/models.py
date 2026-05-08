from django.db import models


from django.db import models


class IL_properties(models.Model):
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
    


class IL_smiles_psi4(models.Model):
    
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
    

class IL_smiles_rdkit(models.Model):
    
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


class metal_anion_energy(models.Model):
    Dimer_Name = models.CharField(max_length=255)
    Dimer_SMILES = models.CharField(max_length=255)
    Component_Name_A = models.CharField(max_length=255)
    Component_SMILES_A = models.CharField(max_length=255)
    Component_Name_B = models.CharField(max_length=255)
    Component_SMILES_B = models.CharField(max_length=255)
    Component_A_Energy_Hatree = models.FloatField()
    Component_B_Energy_Hatree = models.FloatField()
    Component_A_Thermal_correction_to_Gibbs_Free_Energy_Hatree = models.FloatField()
    Component_B_Thermal_correction_to_Gibbs_Free_Energy_Hatree = models.FloatField()
    Component_A_Thermal_correction_to_Enthalpy_Hatree = models.FloatField()
    Component_B_Thermal_correction_to_Enthalpy_Hatree = models.FloatField()
    Component_A_Entropy_J_mol_K = models.FloatField()
    Component_B_Entropy_J_mol_K = models.FloatField()
    Component_A_HOMO_Hatree = models.FloatField()
    Component_B_HOMO_Hatree = models.FloatField()
    Component_A_Dipole_Debye = models.FloatField()
    Component_B_Dipole_Debye = models.FloatField()
    Component_A_LUMO_Hatree = models.FloatField()
    Component_B_LUMO_Hatree = models.FloatField()
    Component_A_Gibbs_Free_Energy_Hatree = models.FloatField()
    Component_A_Enthalpy_Hatree = models.FloatField()
    Component_B_Gibbs_Free_Energy_Hatree = models.FloatField()
    Component_B_Enthalpy_Hatree = models.FloatField()
    Dimer_Energy_Hatree = models.FloatField()
    Dimer_Thermal_correction_to_Gibbs_Free_Energy_Hatree = models.FloatField()
    Dimer_Thermal_correction_to_Enthalpy_Hatree = models.FloatField()
    Dimer_Entropy_J_mol_K = models.FloatField()
    Dimer_HOMO_Hatree = models.FloatField()
    Dimer_Dipole_Debye = models.FloatField()
    Dimer_LUMO_Hatree = models.FloatField()
    Dimer_Gibbs_Free_Energy_Hatree = models.FloatField()
    Dimer_Enthalpy_Hatree = models.FloatField()
    Binding_energy_kJ_mol = models.FloatField()
    Software = models.CharField(
        max_length=255,
        default='Gaussian',
        help_text='Calculation Software'
    )
    Theory_Level = models.CharField(
        max_length=255,
        default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3',
        help_text='Calcualtion Theory Level'
    )
    Source = models.CharField(
        max_length=255,
        default='QC',
        help_text='From Quantum Chemistry Calculation'
    )


class IL(models.Model):
    Name = models.CharField(max_length=255)
    SMILES = models.CharField(max_length=255)
    Energy_Hatree = models.FloatField()
    Thermal_correction_to_Gibbs_Free_Energy_Hatree = models.FloatField()
    Thermal_correction_to_Enthalpy_Hatree = models.FloatField()
    Entropy_J_per_mol_K = models.FloatField()
    HOMO_Hatree = models.FloatField()
    LUMO_Hatree = models.FloatField()
    Dipole_Debye = models.FloatField()
    Gibbs_Free_Energy_Hatree = models.FloatField()
    Enthalpy_Hatree = models.FloatField()
    ECW_V = models.FloatField()
    Software = models.CharField(
        max_length=255,
        default='Gaussian',
        help_text='Calculation Software'
    )
    Theory_Level = models.CharField(
        max_length=255,
        default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3',
        help_text='Calcualtion Theory Level'
    )
    Source = models.CharField(
        max_length=255,
        default='QC',
        help_text='From Quantum Chemistry Calculation'
    )


class Cation(models.Model):
    Name = models.CharField(max_length=255)
    SMILES = models.CharField(max_length=255)
    Energy_Hatree = models.FloatField()
    Thermal_correction_to_Gibbs_Free_Energy_Hatree = models.FloatField()
    Thermal_correction_to_Enthalpy_Hatree = models.FloatField()
    Entropy_J_per_mol_K = models.FloatField()
    HOMO_Hatree = models.FloatField()
    LUMO_Hatree = models.FloatField()
    Dipole_Debye = models.FloatField()
    Gibbs_Free_Energy_Hatree = models.FloatField()
    Enthalpy_Hatree = models.FloatField()
    ECW_V = models.FloatField()
    Software = models.CharField(
        max_length=255,
        default='Gaussian',
        help_text='Calculation Software'
    )
    Theory_Level = models.CharField(
        max_length=255,
        default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3',
        help_text='Calcualtion Theory Level'
    )
    Source = models.CharField(
        max_length=255,
        default='QC',
        help_text='From Quantum Chemistry Calculation'
    )


class Anion(models.Model):
    Name = models.CharField(max_length=255)
    SMILES = models.CharField(max_length=255)
    Energy_Hatree = models.FloatField()
    Thermal_correction_to_Gibbs_Free_Energy_Hatree = models.FloatField()
    Thermal_correction_to_Enthalpy_Hatree = models.FloatField()
    Entropy_J_per_mol_K = models.FloatField()
    HOMO_Hatree = models.FloatField()
    LUMO_Hatree = models.FloatField()
    Dipole_Debye = models.FloatField()
    Gibbs_Free_Energy_Hatree = models.FloatField()
    Enthalpy_Hatree = models.FloatField()
    ECW_V = models.FloatField()
    Software = models.CharField(
        max_length=255,
        default='Gaussian',
        help_text='Calculation Software'
    )
    Theory_Level = models.CharField(
        max_length=255,
        default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3',
        help_text='Calcualtion Theory Level'
    )
    Source = models.CharField(
        max_length=255,
        default='QC',
        help_text='From Quantum Chemistry Calculation'
    )


class Li_electrolyte(models.Model):
    Dimer_Name = models.CharField(max_length=255)
    Dimer_SMILES = models.CharField(max_length=255)
    Component_Name_A = models.CharField(max_length=255)
    Component_SMILES_A = models.CharField(max_length=255)
    Component_Name_B = models.CharField(max_length=255)
    Component_SMILES_B = models.CharField(max_length=255)
    Component_A_Energy_Hatree = models.FloatField()
    Component_B_Energy_Hatree = models.FloatField()
    Component_B_Thermal_correction_to_Gibbs_Free_Energy_Hatree = models.FloatField()
    Component_B_Thermal_correction_to_Enthalpy_Hatree = models.FloatField()
    Component_B_Entropy_J_per_mol_K = models.FloatField()
    Component_A_HOMO_Hatree = models.FloatField()
    Component_B_HOMO_Hatree = models.FloatField()
    Component_A_Dipole_Debye = models.FloatField()
    Component_B_Dipole_Debye = models.FloatField()
    Component_A_LUMO_Hatree = models.FloatField()
    Component_B_LUMO_Hatree = models.FloatField()
    Component_B_Gibbs_Free_Energy_Hatree = models.FloatField()
    Component_B_Enthalpy_Hatree = models.FloatField()
    Dimer_Energy_Hatree = models.FloatField()
    Dimer_Thermal_correction_to_Gibbs_Free_Energy_Hatree = models.FloatField()
    Dimer_Thermal_correction_to_Enthalpy_Hatree = models.FloatField()
    Dimer_Entropy_J_per_mol_K = models.FloatField()
    Dimer_HOMO_Hatree = models.FloatField()
    Dimer_LUMO_Hatree = models.FloatField()
    Dimer_Dipole_Debye = models.FloatField()
    Dimer_Gibbs_Free_Energy_Hatree = models.FloatField()
    Dimer_Enthalpy_Hatree = models.FloatField()
    Binding_energy_kJ_per_mol = models.FloatField()
    Software = models.CharField(
        max_length=255,
        default='Gaussian',
        help_text='Calculation Software'
    )
    Theory_Level = models.CharField(
        max_length=255,
        default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3',
        help_text='Calcualtion Theory Level'
    )
    Source = models.CharField(
        max_length=255,
        default='QC',
        help_text='From Quantum Chemistry Calculation'
    )


class electrolyte(models.Model):
    Component_Name_B = models.CharField(max_length=255)
    Component_SMILES_B = models.CharField(max_length=255)
    Component_B_Energy_Hatree = models.FloatField()
    Component_B_Thermal_correction_to_Gibbs_Free_Energy_Hatree = models.FloatField()
    Component_B_Thermal_correction_to_Enthalpy_Hatree = models.FloatField()
    Component_B_Entropy_J_per_mol_K = models.FloatField()
    Component_B_HOMO_Hatree = models.FloatField()
    Component_B_LUMO_Hatree = models.FloatField()
    Component_B_Dipole_Debye = models.FloatField()
    Component_B_Gibbs_Free_Energy_Hatree = models.FloatField()
    Component_B_Enthalpy_Hatree = models.FloatField()
    Component_B_ECW_V = models.FloatField()
    Software = models.CharField(
        max_length=255,
        default='Gaussian',
        help_text='Calculation Software'
    )
    Theory_Level = models.CharField(
        max_length=255,
        default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3',
        help_text='Calcualtion Theory Level'
    )
    Source = models.CharField(
        max_length=255,
        default='QC',
        help_text='From Quantum Chemistry Calculation'
    )


class ILgenerator_IL(models.Model):
    Name = models.CharField(max_length=255)
    SMILES = models.CharField(max_length=255)
    Anion_Name = models.CharField(max_length=255)
    Cation_Name = models.CharField(max_length=255)
    Cation_SMILES_type = models.CharField(max_length=255)
    Anion_SMILES = models.CharField(max_length=255)
    Cation_SMILES = models.CharField(max_length=255)
    conductivity = models.FloatField()
    Ea = models.FloatField()
    lnA = models.FloatField()
    Tm = models.FloatField()
    ECW = models.FloatField()
    ILScore = models.FloatField()

class Example(models.Model):
    X1=models.CharField(max_length=255)
    X2=models.CharField(max_length=255)
    X3=models.CharField(max_length=255)
    X4=models.CharField(max_length=255)


class IL_ML_data(models.Model):
    Name = models.CharField(max_length=255,null=True,blank=True)
    SMILES = models.CharField(max_length=255,null=True,blank=True)
    Anion_SMILES = models.CharField(max_length=255,null=True,blank=True)
    Cation_SMILES = models.CharField(max_length=255,null=True,blank=True)
    Cation_SMILES_type = models.CharField(max_length=255,null=True,blank=True)
    Anion_SMILES_type = models.CharField(max_length=255,null=True,blank=True)
    Conductivity_mS_per_cm = models.FloatField(null=True,blank=True)
    Tm_K = models.FloatField(null=True,blank=True)
    ECW_V = models.FloatField(null=True,blank=True)
    Type = models.CharField(max_length=255,null=True,blank=True)
    Source = models.CharField(
        max_length=255,
        default='ML',
        help_text='Predicted From ML Model'
    )

class Cation_QC_data(models.Model):
    Name = models.CharField(max_length=255,null=True,blank=True)
    SMILES = models.CharField(max_length=255,null=True,blank=True)
    Cation_type = models.CharField(max_length=255,null=True,blank=True)
    Energy_Hatree = models.FloatField(null=True,blank=True)
    Thermal_correction_to_Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    Thermal_correction_to_Enthalpy_Hatree = models.FloatField(null=True,blank=True)
    Entropy_J_per_mol_K = models.FloatField(null=True,blank=True)
    HOMO_Hatree = models.FloatField(null=True,blank=True)
    LUMO_Hatree = models.FloatField(null=True,blank=True)
    Dipole_Debye = models.FloatField(null=True,blank=True)
    Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    Enthalpy_Hatree = models.FloatField(null=True,blank=True)
    HOMO_LUMO_Gap_eV = models.FloatField(null=True,blank=True)
    Software = models.CharField(
        max_length=255,
        default='Gaussian',
        help_text='Calculation Software'
    )
    Theory_Level = models.CharField(
        max_length=255,
        default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3',
        help_text='Calcualtion Theory Level'
    )
    Source = models.CharField(
        max_length=255,
        default='QC',
        help_text='From Quantum Chemistry Calculation'
    )

class Anion_QC_data(models.Model):
    Name = models.CharField(max_length=255,null=True,blank=True)
    SMILES = models.CharField(max_length=255,null=True,blank=True)
    Anion_type = models.CharField(max_length=255,null=True,blank=True)
    Energy_Hatree = models.FloatField(null=True,blank=True)
    Thermal_correction_to_Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    Thermal_correction_to_Enthalpy_Hatree = models.FloatField(null=True,blank=True)
    Entropy_J_per_mol_K = models.FloatField(null=True,blank=True)
    HOMO_Hatree = models.FloatField(null=True,blank=True)
    LUMO_Hatree = models.FloatField(null=True,blank=True)
    Dipole_Debye = models.FloatField(null=True,blank=True)
    Gibbs_Free_Energy_Hatree = models.FloatField(null=True,blank=True)
    Enthalpy_Hatree = models.FloatField(null=True,blank=True)
    HOMO_LUMO_Gap_eV = models.FloatField(null=True,blank=True)
    Software = models.CharField(
        max_length=255,
        default='Gaussian',
        help_text='Calculation Software'
    )
    Theory_Level = models.CharField(
        max_length=255,
        default='opt+freq: b3lyp/6-311G** em=gd3bj\nenergy: M062X/6-311G+(2d, p) em=gd3',
        help_text='Calcualtion Theory Level'
    )
    Source = models.CharField(
        max_length=255,
        default='QC',
        help_text='From Quantum Chemistry Calculation'
    )

class IL_Tm_conductivity_ECW_data(models.Model):
    Name = models.CharField(max_length=255,null=True,blank=True)
    SMILES = models.CharField(max_length=255,null=True,blank=True)
    Anion_SMILES = models.CharField(max_length=255,null=True,blank=True)
    Cation_SMILES = models.CharField(max_length=255,null=True,blank=True)
    Cation_SMILES_type = models.CharField(max_length=255,null=True,blank=True)
    Anion_SMILES_type = models.CharField(max_length=255,null=True,blank=True)
    Conductivity_mS_per_cm = models.FloatField(null=True,blank=True)
    Tm_K = models.FloatField(null=True,blank=True)
    ECW_V = models.FloatField(null=True,blank=True)
    Type = models.CharField(max_length=255,null=True,blank=True)
    Source = models.CharField(
        max_length=255,
        default='QC and EXP',
        help_text='ECW From QC, Tm and Conductivity from EXP'
    )