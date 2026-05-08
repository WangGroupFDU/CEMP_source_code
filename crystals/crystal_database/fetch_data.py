import pandas as pd
from mp_api.client import MPRester
from pandas import DataFrame

fields_not_requested=['material_id','is_magnetic', 'ordering', 'total_magnetization',
                                                           'builder_meta', 'nsites', 'elements', 'nelements',
                                                           'composition', 'composition_reduced', 'formula_pretty',
                                                           'formula_anonymous', 'chemsys', 'volume',
                                                           'density', 'density_atomic', 'symmetry',
                                                           'property_name', 'deprecated', 'deprecation_reasons',
                                                           'last_updated', 'origins', 'warnings', 'structure', 'task_ids',
                                                           'uncorrected_energy_per_atom', 'energy_per_atom',
                                                           'formation_energy_per_atom', 'energy_above_hull',
                                                           'is_stable', 'equilibrium_reaction_energy_per_atom',
                                                           'decomposes_to', 'xas', 'grain_boundaries', 'band_gap', 'cbm',
                                                           'vbm', 'efermi', 'is_gap_direct', 'is_metal', 'es_source_calc_id',
                                                           'bandstructure', 'dos', 'dos_energy_up', 'dos_energy_down',
                                                           'total_magnetization_normalized_vol', 'total_magnetization_normalized_formula_units',
                                                           'num_magnetic_sites', 'num_unique_magnetic_sites',
                                                           'types_of_magnetic_species', 'k_voigt', 'k_reuss', 'k_vrh',
                                                           'g_voigt', 'g_reuss', 'g_vrh', 'universal_anisotropy',
                                                           'homogeneous_poisson', 'e_total', 'e_ionic', 'e_electronic',
                                                           'n', 'e_ij_max', 'weighted_surface_energy_EV_PER_ANG2',
                                                           'weighted_surface_energy', 'weighted_work_function',
                                                           'surface_anisotropy', 'shape_factor', 'has_reconstructed',
                                                           'possible_species', 'has_props', 'theoretical']


def fetch_data_element(element):
    with MPRester("BhxGe6a92hXHlEYNhc2jJp4fTytK9kKy") as mpr:
        
        docs = mpr.summary.search(elements=element, fields = fields_not_requested)
    
    
    keys = []
    values = []
    label = []

    for doc in docs:
        for field in doc:
            
            if field[0] != "fields_not_requested":
                if field[0] == "material_id":
                    for i in range(0, len(fields_not_requested)):
                        label.append(field[1])
                else:
                    pass
                keys.append(field[0])
                values.append(field[1])
            else:
                pass

    
    
    print(len(keys), len(values), len(label))
    results = DataFrame({"keys": keys, "values": values, "label":label})
    print(results.head())
    
    
    pivot_table = results.pivot(values='values', index='label', columns='keys')
    print(pivot_table)
    pivot_table = pivot_table.reset_index()
    print(pivot_table["chemsys"])
    pivot_table.to_csv(element[0]+"_crystal.csv")


elements = [['Li'],['Na'],['K'],['Al'],['Ca'],['Mg'],['Zn'],['Ba']]

for element in elements:
    fetch_data_element(element)





