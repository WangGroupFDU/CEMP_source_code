# Public Algorithm Inventory

## Scope

The public release contains only notebooks that are reachable from a CEMP page,
API, task executor, or maintained prediction example. The inventory contains
118 ordered workflow notebooks and 5 prediction notebooks. Old copies, local
duplicates, test notebooks, `Run_All` wrappers, conversion utilities, and
unreferenced experimental notebooks are not part of the release.

The machine-readable allowlist is
`autocompute/public_algorithm_inventory.py`. The release verifier compares every
tracked `.ipynb` file with that allowlist and fails when a required notebook is
missing or an unregistered notebook is present.

## Execution Model

For an AutoCompute task, CEMP creates a task directory, copies the selected
workflow directory and `cemp_software_settings.py` into it, and executes the
listed notebooks in order with `jupyter nbconvert --execute`. A failed stage
writes `failure.txt` and stops the sequence. A successful sequence writes
`success.txt` and returns the generated files to the task directory.

The shared configuration module reads environment variables and, when present,
`/etc/cemp/CEMPsettings.ini`. Environment variables take precedence. External
software is not included in this repository.

## Molecular-Dynamics Workflows

| Task type | Source directory | Execution function | Notebook order | External software |
| --- | --- | --- | --- | --- |
| `MDCoumpute` | `autocompute/static/MDAutocompute_programe/` | `autocompute.remote_utils.run_Gromacs_MD_notebook_tasks_remote` | `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `11`, `12`, `13` | Gaussian 16, GROMACS, Sobtop, Multiwfn, Open Babel, VMD |
| `MDCoumpute_ORCA` | `autocompute/static/MDAutocompute_programe_ORCA/` | `autocompute.run_MD_QC_utils.run_Gromacs_MD_notebook_tasks_ORCA` | `1`, `2`, `3`, `4`, `5`, `6`, `8`, `9` | ORCA, GROMACS, Sobtop, Multiwfn, Open Babel, Open MPI, VMD |

The numbered stages cover repeat-unit charge preparation, polymer construction,
topology generation, quantum-chemistry input and optimization, MD preparation
and execution, trajectory analysis, component-energy analysis, solvent-cage
escape analysis, and coordination-environment analysis. The exact filenames are
listed in `STANDARD_MD_NOTEBOOKS` and `ORCA_MD_NOTEBOOKS` in the machine-readable
inventory.

## Quantum-Chemistry Workflows

| Task type | Source directory | Execution function | Ordered stages | External software |
| --- | --- | --- | --- | --- |
| `HTQC_single_point_energy` | `autocompute/static/QcAutocompute_programe/HTQC_single_point_energy/` | `autocompute.remote_utils.run_Gaussian_single_point_energy_notebook_tasks_remote` | Gaussian stages `1` through `7` | Gaussian 16, Multiwfn |
| `HTQC_binding_energy` | `autocompute/static/QcAutocompute_programe/HTQC_binding_energy/` | `autocompute.remote_utils.run_Gaussian_binding_energy_notebook_tasks_remote` | Component `1`-`7`, dimer `1`-`7`, then `Data_processing` | Gaussian 16, Multiwfn |
| `HTQC_pka_pkb_calculation` | `autocompute/static/QcAutocompute_programe/HTQC_pka_pkb/` | `autocompute.remote_utils.run_Gaussian_pka_pkb_notebook_tasks_remote` | `pkb_DFT_1` through `pkb_DFT_7` | Gaussian 16, Multiwfn |
| `HTQC_ox_red_calculation` | `autocompute/static/QcAutocompute_programe/HTQC_ox_red/` | `autocompute.remote_utils.run_Gaussian_ox_red_notebook_tasks_remote` | `ox_red_1` through `ox_red_7` | Gaussian 16, Multiwfn |
| `HTQC_reaction_thermo_properties_calculation` | `autocompute/static/QcAutocompute_programe/HTQC_reaction_thermo/` | `autocompute.remote_utils.run_Gaussian_reaction_thermo_notebook_tasks_remote` | `reaction_thermo_1` through `reaction_thermo_6` | Gaussian 16, Multiwfn |
| `HTQC_global_reaction_properties_descriptors_calculation` | `autocompute/static/QcAutocompute_programe/HTQC_global_reaction_descriptors_calculation/` | `autocompute.remote_utils.run_Gaussian_global_reaction_properties_notebook_tasks_remote` | `reaction_1` through `reaction_6` | Gaussian 16, Multiwfn |
| `HTQC_single_point_energy_orca` | `autocompute/static/QcAutocompute_programe/ORCA_HTQC_single_point_energy/` | `autocompute.remote_utils.run_ORCA_single_point_energy_notebook_tasks_remote` | ORCA stages `1` through `5` | ORCA, Open MPI, Multiwfn |
| `HTQC_binding_energy_orca` | `autocompute/static/QcAutocompute_programe/ORCA_HTQC_binding_energy/` | `autocompute.remote_utils.run_ORCA_binding_energy_notebook_tasks_remote` | Component `1`-`5`, then dimer `1`-`5` | ORCA, Open MPI, Multiwfn |
| `HTQC_ox_red_calculation_orca` | `autocompute/static/QcAutocompute_programe/ORCA_HTQC_ox_red/` | `autocompute.remote_utils.run_ORCA_ox_red_notebook_tasks_remote` | `ORCA_ox_red_1` through `ORCA_ox_red_5` | ORCA, Open MPI, Multiwfn |
| `Manual_Mode_QCcompute` | `autocompute/static/QcAutocompute_programe/ORCA_manual_mode_opt+freq_energy/` | `autocompute.remote_utils.run_ORCA_manual_notebook_tasks_remote` | Optimization/frequency `2`, imaginary-frequency correction `3`, energy `4`, extraction `5` | ORCA, Open MPI, Multiwfn |
| `Manual_Mode_QCcompute_energy` | `autocompute/static/QcAutocompute_programe/ORCA_manual_mode_energy/` | `autocompute.remote_utils.run_ORCA_manual_notebook_tasks_remote_energy` | Energy `1`, extraction `2` | ORCA, Open MPI |

The `qc_database_utils.py` files beside these workflows and
`md_qc_database_utils.py` beside the standard MD workflow are executable helper
modules imported by the notebooks. They are included in the release allowlist
and parsed by the release verifier.

## Analysis And Query Workflows

| Task type | Source directory and notebook | Execution function | External software |
| --- | --- | --- | --- |
| `DrawESP` | `autocompute/static/drawESP/auto_draw_ESP.ipynb` | `autocompute.remote_utils.run_draw_ESP_notebook_tasks_remote` | Gaussian 16, Multiwfn, VMD |
| `DrawESP_remote` | `autocompute/static/drawESP/auto_draw_ESP_gbw.ipynb` | `autocompute.remote_utils.run_draw_ESP_notebook_tasks_gbw_remote` | ORCA, Multiwfn, VMD |
| `Draw_HOMO_LUMO_orb` | `autocompute/static/draw_HOMO_LUMO_orb/draw_HOMO_LUMO_orb.ipynb` | `autocompute.remote_utils.run_draw_HOMO_LUMO_orb_notebook_tasks_remote` | Multiwfn, VMD |
| `NCI_analysis` | `autocompute/static/NCIanalysis/NCI_analysis.ipynb` | `autocompute.remote_utils.run_NCI_SCF_analysis_notebook_tasks_remote` | Gaussian 16, Multiwfn, VMD |
| `NCI_promolecular_analysis` | `autocompute/static/NCI_analysis_promolecular/NCI_analysis_promolecular.ipynb` | `autocompute.remote_utils.run_NCI_promolecular_analysis_notebook_tasks_remote` | Multiwfn, VMD |
| `From SMILES to Name` | `autocompute/static/query_SMILES/query_simliar_monomer.ipynb` | `autocompute.run_MD_QC_utils.run_query_name_CAS_tasks` | Open Babel |

Each analysis or query entry is a one-notebook workflow.

## Polymer-Generation Workflows

The six maintained polymer-generation directories are:

```text
polymer/static/programe/generate_homopolymer/
polymer/static/programe/generate_random_copolymer/
polymer/static/programe/generate_block_copolymer/
polymer/static/programe/generate_cyclic_homopolymer/
polymer/static/programe/generate_cyclic_random_copolymer/
polymer/static/programe/generate_cyclic_block_copolymer/
```

Every directory uses the same three-stage order:

```text
1_Polymer_RESP_repeat_unit.ipynb
2_Polymer_chg_and_Polymer_creation_Linear_polymer.ipynb
3_create_Polymer_itp_top.ipynb
```

The page selects the linear or cyclic directory and dispatches
`polymer.remote_utils.generate_polymer_run_notebook_tasks_remote`. These
workflows use Gaussian 16, GROMACS, Sobtop, Multiwfn, and Open Babel. The current
step 2 and step 3 notebooks include the maintained Sobtop MOL2/topology repair.

## Prediction Notebooks

| Example | Location | Runtime assets |
| --- | --- | --- |
| Ionic-liquid CPU inference | `ionic_liquid/static/model/prediction_model.ipynb` | `CEMP_IL_MODEL_DIR` or `ionic_liquid/static/model/` |
| Single ionic-liquid SMILES prediction | `ionic_liquid/static/program/predict_IL_properties_SMILES_single/1_IL_predict_with_xgboost.ipynb` | `CEMP_IL_MODEL_DIR` or `ionic_liquid/static/model/` |
| Batch ionic-liquid spreadsheet prediction | `ionic_liquid/static/program/predict_IL_properties_excel_batch/1_IL_predict_with_xgboost.ipynb` | `CEMP_IL_MODEL_DIR` or `ionic_liquid/static/model/` |
| Copolymer property prediction | `polymer/static/programe/predict_copolymer_property/1_predict_copolymer_property.ipynb` | `CEMP_POLYMER_MODEL_DIR` or `polymer/static/model/` |
| Polymer property prediction | `polymer/static/programe/predict_polymer_properties/predict_polymer_property.ipynb` | `CEMP_POLYMER_MODEL_DIR` or `polymer/static/model/` |

The first notebook is a standalone CPU inference example and does not require a
running CEMP web server. Extract the public model archive at the repository root
before running any prediction notebook.

## Validation

Run the inventory and source checks with:

```bash
python manage.py verify_public_release --manifest data/public_manifest.json
```

The command checks the exact notebook count, allowlist membership, JSON and
Python syntax, cleared outputs and execution counts, helper-module syntax,
shared configuration parsing, release placeholders, and known production paths.
