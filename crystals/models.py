from django.db import models


from django.db import models


class Crystal_properties(models.Model):
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
    


class Crystal_smiles_psi4(models.Model):
    
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
    

class Crystal_smiles_rdkit(models.Model):
    
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


class Crystal(models.Model):
    crystal=models.CharField(max_length=25)
    label=models.CharField(max_length=25)
    band_gap=models.DecimalField(max_digits=25, decimal_places=3)
    chemsys=models.CharField(max_length=25)
    density=models.DecimalField(max_digits=25, decimal_places=3)
    density_atomic=models.DecimalField(max_digits=25, decimal_places=3)
    deprecated=models.CharField(max_length=25)
    efermi=models.DecimalField(max_digits=25, decimal_places=3)
    energy_above_hull=models.DecimalField(max_digits=25, decimal_places=5)
    energy_per_atom=models.DecimalField(max_digits=25, decimal_places=3)
    formation_energy_per_atom=models.DecimalField(max_digits=25, decimal_places=5)
    formula_anonymous=models.CharField(max_length=25)
    formula_pretty=models.CharField(max_length=25)
    is_gap_direct=models.CharField(max_length=25)
    is_magnetic=models.CharField(max_length=25)
    is_metal=models.CharField(max_length=25)
    is_stable=models.CharField(max_length=25)
    nelements=models.SmallIntegerField()
    nsites=models.SmallIntegerField()
    num_magnetic_sites=models.SmallIntegerField()
    num_unique_magnetic_sites=models.SmallIntegerField()
    ordering=models.CharField(max_length=25)
    theoretical=models.CharField(max_length=25)
    total_magnetization=models.DecimalField(max_digits=25, decimal_places=3)
    
    
    
    volume=models.DecimalField(max_digits=25, decimal_places=3)

