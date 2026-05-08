import pandas as pd
from ionic_liquid.models import IL_properties, IL_smiles_psi4, IL_smiles_rdkit
import traceback


dataset = pd.read_csv("ionic_liquid/ionic_liquid_database_rawfile/dataset_iolitech_type.csv", index_col = False)
dataset = dataset.fillna(0)
for i in range(0, len(dataset)):
    print(dataset["label"][i])
    IL_Properties = IL_properties(label=dataset["label"][i],
                                  formula=dataset["formula"][i],
                                  cation = dataset["cation"][i],
                                  anion = dataset["anion"][i],
                                  cation_type = dataset["cation_type"][i],
                                  anion_type = dataset["anion_type"][i],
                                  ECW = dataset["ECW"][i],
                                  melting_point = dataset["melting_point"][i],
                                  conductivity = dataset["conductivity"][i],
                                  viscosity = dataset["viscosity"][i],
                                  density = dataset["density"][i],
                                  T_conductivity = dataset["T_conductivity"][i],
                                  T_viscosity = dataset["T_viscosity"][i],
                                  T_density = dataset["T_density"][i],
                                  conductivity_norm = dataset["conductivity_norm"][i],
                                  viscosity_norm = dataset["viscosity_norm"][i],
                                  density_norm = dataset["density_norm"][i]
                                  )
    try:
        IL_Properties.save()
    except Exception:
        print(traceback.format_exc())
        print("Error loading in line", i)



dataset = pd.read_csv("ionic_liquid/ionic_liquid_database_rawfile/IL_smiles_rdkit.csv", index_col = False)
dataset = dataset.fillna(0)
for i in range(0, len(dataset)):
    object = IL_smiles_rdkit(name=dataset["name"][i],
                                  smile_form=dataset["smile_form"][i],
                                  Asphericity = dataset["Asphericity"][i],
                                  Eccentricity = dataset["Eccentricity"][i],
                                  NPR1 = dataset["NPR1"][i],
                                  NPR2 = dataset["NPR2"][i],
                                  PMI1 = dataset["PMI1"][i],
                                  PMI2 = dataset["PMI2"][i],
                                  PMI3 = dataset["PMI3"][i],
                                  RadiusOfGyration = dataset["RadiusOfGyration"][i],
                                  SpherocityIndex = dataset["SpherocityIndex"][i],
                                  ExactMolWt = dataset["ExactMolWt"][i],
                                  FpDensityMorgan1 = dataset["FpDensityMorgan1"][i],
                                  FpDensityMorgan2 = dataset["FpDensityMorgan2"][i],
                                  HeavyAtomMolWt = dataset["HeavyAtomMolWt"][i],
                                  MaxAbsPartialCharge = dataset["MaxAbsPartialCharge"][i],
                                  MaxPartialCharge = dataset["MaxPartialCharge"][i],
                                  MinPartialCharge = dataset["MinPartialCharge"][i],
                                  NumRadicalElectrons = dataset["NumRadicalElectrons"][i],
                                  NumValenceElectrons = dataset["NumValenceElectrons"][i],
                                  volume = dataset["volume"][i],
                                  type = dataset["type"][i]
                                  )
    try:
        object.save()
    except Exception:
        print(traceback.format_exc())
        print("Error loading in line", i)



dataset = pd.read_csv("ionic_liquid/ionic_liquid_database_rawfile/IL_smiles_psi4.csv", index_col = False)
dataset = dataset.fillna(0)
for i in range(0, len(dataset)):
    object = IL_smiles_psi4(name=dataset["name"][i],
                                  smile_form=dataset["smile_form"][i],
                                  energy = dataset["energy"][i],
                                  HOMO = dataset["HOMO"][i],
                                  LUMO = dataset["LUMO"][i],
                                  dipole_x = dataset["dipole_x"][i],
                                  dipole_y = dataset["dipole_y"][i],
                                  dipole_z = dataset["dipole_z"][i],
                                  dipole_total = dataset["dipole_total"][i],
                                  type = dataset["type"][i]
                                  )
    try:
        object.save()
    except Exception:
        print(traceback.format_exc())
        print("Error loading in line", i)



