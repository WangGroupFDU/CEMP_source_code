
from __future__ import annotations

from typing import Dict, List, Optional



GAUSSIAN_HTQC = "gaussian_htqc"
ORCA_HTQC = "orca_htqc"
MD_GROMACS_GAUSSIAN = "md_gromacs_gaussian"
VISUALIZATION_ANALYSIS = "visualization_analysis"
MARKOV_ANALYSIS = "markov_analysis"
POLYMER_GENERATION = "polymer_generation"



TASK_TYPE_TO_CAPABILITY: Dict[str, str] = {
    "HTQC_single_point_energy": GAUSSIAN_HTQC,
    "HTQC_binding_energy": GAUSSIAN_HTQC,
    "HTQC_pka_pkb_calculation": GAUSSIAN_HTQC,
    "HTQC_ox_red_calculation": GAUSSIAN_HTQC,
    "HTQC_reaction_thermo_properties_calculation": GAUSSIAN_HTQC,
    "HTQC_global_reaction_properties_descriptors_calculation": GAUSSIAN_HTQC,
    "HTQC_single_point_energy_orca": ORCA_HTQC,
    "HTQC_binding_energy_orca": ORCA_HTQC,
    "HTQC_ox_red_calculation_orca": ORCA_HTQC,
    "Manual_Mode_QCcompute": ORCA_HTQC,
    "Manual_Mode_QCcompute_energy": ORCA_HTQC,
    "MDCoumpute": MD_GROMACS_GAUSSIAN,
    "DrawESP": VISUALIZATION_ANALYSIS,
    "DrawESP_remote": VISUALIZATION_ANALYSIS,
    "Draw_HOMO_LUMO_orb": VISUALIZATION_ANALYSIS,
    "NCI_analysis": VISUALIZATION_ANALYSIS,
    "NCI_promolecular_analysis": VISUALIZATION_ANALYSIS,
    "Markov_GDyNet_analysis": MARKOV_ANALYSIS,
    "Generate_homopolymer": POLYMER_GENERATION,
    "Generate_random_copolymer": POLYMER_GENERATION,
    "Generate_block_copolymer": POLYMER_GENERATION,
}



DEPRECATED_REMOTE_TASK_TYPES = {
    "MDCoumpute_ORCA",
}



LOCAL_ONLY_TASK_TYPES = {
    "From SMILES to Name",
}



CAPABILITY_REQUIRED_SETTINGS_KEYS: Dict[str, List[str]] = {
    GAUSSIAN_HTQC: [
        "gaussian16_bin",
        "gaussian16_formchk",
        "gaussian_database_path",
    ],
    ORCA_HTQC: [
        "orca_path",
        "orca_database_path",
    ],
    MD_GROMACS_GAUSSIAN: [
        "gmx_bin",
        "gaussian16_bin",
        "gaussian16_formchk",
        "multiwfn_exe",
        "sobtop_home",
    ],
    
    VISUALIZATION_ANALYSIS: [
        "multiwfn_exe",
    ],
    
    MARKOV_ANALYSIS: [],
    POLYMER_GENERATION: [
        "gaussian16_bin",
        "gaussian16_formchk",
        "multiwfn_exe",
        "sobtop_home",
    ],
}



TASK_TYPE_ADDITIONAL_SETTINGS_KEYS: Dict[str, List[str]] = {
    "DrawESP": ["gaussian16_formchk"],
    "DrawESP_remote": ["orca_path"],
    "Draw_HOMO_LUMO_orb": [],
    "NCI_analysis": ["gaussian16_formchk"],
    "NCI_promolecular_analysis": [],
}


def get_required_capability(task_type: str) -> Optional[str]:

    if task_type in LOCAL_ONLY_TASK_TYPES:
        return None
    return TASK_TYPE_TO_CAPABILITY.get(task_type)


def is_deprecated_remote_task_type(task_type: str) -> bool:

    return task_type in DEPRECATED_REMOTE_TASK_TYPES


def get_required_settings_keys_for_task(task_type: str) -> List[str]:

    capability = get_required_capability(task_type)
    if capability is None:
        return []

    merged: List[str] = []
    for key in CAPABILITY_REQUIRED_SETTINGS_KEYS.get(capability, []):
        if key not in merged:
            merged.append(key)
    for key in TASK_TYPE_ADDITIONAL_SETTINGS_KEYS.get(task_type, []):
        if key not in merged:
            merged.append(key)
    return merged
