from django.urls import path, include, re_path

from . import views
from .views import (
    ElectrolyteListView,
    ElectrolyteDetailView,
    CationListView,
    AnionListView,
    Metal_Anion_EnergyListView,
    Li_ElectrolyteListView,
    Metal_Anion_EnergyDetailView,
    CationDetailView,
    AnionDetailView,
    Li_ElectrolyteDetailView,
)


SPA_EXCLUDE_PATTERNS = [
    "api/",
    "smilesdrawer",
    "Database",
    "QCcompute",
    "MDCompute",
    "Visualization",
    "MDVisualization",
    "query_smiles_name",
    "process_upload_smiles_file",
    "from_smiles_get_name_page",
    "draw_ESP_page",
    "draw_ESP_func",
    "draw_ESP_func_gbw",
    "draw_HOMO_LUMO_orb_page",
    "draw_HOMO_LUMO_orb_func",
    "NCI_analysis_page",
    "NCI_analysis_func",
    "NCI_analysis_promolecular_func",
]
SPA_CATCHALL_PATTERN = "|".join(SPA_EXCLUDE_PATTERNS)

app_name = "autocompute"  

urlpatterns = [
    
    
    path("", views.spa_index, name="index"),
    
    re_path(r"^assets/(?P<path>.*)$", views.spa_assets, name="spa_assets"),
    
    re_path(
        r"^(?P<filename>[\w\-\.]+\.(xlsx|pdf|png|gif|jpg|jpeg|svg)|ketcher/.+)$",
        views.spa_static,
        name="spa_static",
    ),
    
    
    path("smilesdrawer", views.SMILESDrawer, name="SMILESDrawer"),
    
    path("Database", views.database, name="Database"),
    path("QCcompute", views.QCcompute_base, name="QcCompute_base"),
    path(
        "HTQC_single_point", views.HTQC_single_point, name="QcCompute_HTQC_single_point"
    ),
    path(
        "HTQC_binding_energy",
        views.HTQC_binding_energy,
        name="QcCompute_HTQC_binding_energy",
    ),
    path("HTQC_pka_pkb", views.HTQC_pka_pkb, name="QcCompute_HTQC_pka_pkb"),
    path(
        "HTQC_pka_pkb/predict_conjugate_acid_base/",
        views.predict_conjugate_acid_base,
        name="predict_conjugate_acid_base",
    ),
    path("HTQC_ox_red", views.HTQC_ox_red, name="QcCompute_HTQC_ox_red"),
    path(
        "HTQC_reaction_thermo", views.HTQC_reaction_thermo, name="HTQC_reaction_thermo"
    ),
    path(
        "HTQC_global_reaction_properties",
        views.HTQC_global_reaction_properties,
        name="HTQC_global_reaction_properties",
    ),
    path("MDCompute", views.mdcompute, name="MDCompute"),
    path("jsmol_test", views.jsmol_test, name="jsmol_test"),
    path(
        "QCcompute/transfer_tool",
        views.transfer_tool_page_view,
        name="transfer_tool_page",
    ),  
    path(
        "QCcompute/process_transfer_chk2fchk",
        views.convert_chk_to_fchk_view,
        name="convert_chk_to_fchk",
    ),  
    path(
        "QCcompute/process_transfer_gbw2molden",
        views.convert_gbw_to_molden_view,
        name="convert_gbw_to_molden",
    ),  
    
    path("Database/example", views.example_view, name="example"),
    path("Database/Cation", views.Cation_view, name="Cation"),
    path("Database/Anion", views.Anion_view, name="Anion"),
    path("Database/IL", views.IL_view, name="IL"),
    
    path("Visualization", views.Visualization, name="Visualization"),
    path(
        "visualization/molecule_visualization_upload",
        views.molecule_visualization_upload,
        name="molecule_visualization_upload",
    ),
    
    path("MDcompute/MDVisualization", views.MDVisualization, name="MDVisualization"),
    
    path("Database/electrolyte", views.electrolyte_view_paging, name="electrolyte"),
    path(
        "Database/get_molecule_file/", views.get_molecule_file, name="get_molecule_file"
    ),
    path(
        "Database/Li_electrolyte",
        views.Li_electrolyte_view_paging,
        name="Li_electrolyte",
    ),
    path("Database/Salt", views.render_metal_anion_energy_view, name="Salt"),
    path(
        "QCcompute/upload_excel_HTQC_single_point_energy",
        views.upload_excel_QcCoumpute_HTQC_single_point_energy,
        name="upload_excel_QcCoumpute_HTQC_single_point_energy",
    ),
    path(
        "QCcompute/upload_excel_HTQC_binding_energy",
        views.upload_excel_QcCoumpute_HTQC_binding_energy,
        name="upload_excel_QcCoumpute_HTQC_binding_energy",
    ),
    path(
        "QCcompute/upload_excel_HTQC_pka_pkb",
        views.upload_excel_QcCoumpute_HTQC_pka_pkb,
        name="upload_excel_QcCoumpute_HTQC_pka_pkb",
    ),
    path(
        "QCcompute/upload_excel_HTQC_ox_red",
        views.upload_excel_QcCoumpute_HTQC_ox_red,
        name="upload_excel_QcCoumpute_HTQC_ox_red",
    ),
    path(
        "QCcompute/upload_excel_HTQC_reaction_thermo",
        views.upload_excel_QcCoumpute_HTQC_reaction_thermo,
        name="upload_excel_QcCoumpute_HTQC_reaction_thermo",
    ),
    path(
        "QCcompute/upload_excel_HTQC_global_reaction_properties",
        views.upload_excel_QcCoumpute_HTQC_global_reaction_properties,
        name="upload_excel_QcCoumpute_HTQC_global_reaction_properties",
    ),
    
    path(
        "QCcompute/process_excel_HTQC_binding_energy_byurl",
        views.process_excel_QcCoumpute_HTQC_binding_energy_byurl,
        name="process_excel_QcCoumpute_HTQC_binding_energy_byurl",
    ),
    path(
        "QCcompute/process_excel_HTQC_single_point_energy_byurl",
        views.process_excel_QcCoumpute_HTQC_single_point_energy_byurl,
        name="process_excel_QcCoumpute_HTQC_single_point_energy_byurl",
    ),
    path(
        "QCcompute/process_excel_HTQC_pka_pkb_byurl",
        views.process_excel_QcCoumpute_HTQC_pka_pkb,
        name="process_excel_QcCoumpute_HTQC_pka_pkb",
    ),
    path(
        "QCcompute/process_excel_HTQC_ox_red_byurl",
        views.process_excel_QcCoumpute_HTQC_ox_red,
        name="process_excel_HTQC_reaction_thermo",
    ),
    path(
        "QCcompute/process_excel_HTQC_reaction_thermo_byurl",
        views.process_excel_HTQC_reaction_thermo,
        name="process_excel_HTQC_reaction_thermo",
    ),
    path(
        "QCcompute/process_excel_HTQC_global_reaction_properties_byurl",
        views.process_excel_HTQC_global_reaction_properties,
        name="process_excel_HTQC_global_reaction_properties",
    ),
    path(
        "QCcompute/opt_progress_status",
        views.opt_progress_status_QcCoumpute,
        name="opt_progress_status_QcCoumpute",
    ),
    path(
        "QCcompute/energy_progress_status",
        views.energy_progress_status_QcCoumpute,
        name="energy_progress_status_QcCoumpute",
    ),
    
    path(
        "QCcompute/process_excel_HTQC_single_point_energy_byurl_orca",
        views.process_excel_QcCoumpute_HTQC_single_point_energy_byurl_orca,
        name="process_excel_QcCoumpute_HTQC_single_point_energy_byurl_orca",
    ),
    
    path(
        "QCcompute/process_excel_HTQC_binding_energy_byurl_orca",
        views.process_excel_QcCoumpute_HTQC_binding_energy_byurl_orca,
        name="process_excel_QcCoumpute_HTQC_binding_energy_byurl_orca",
    ),
    
    path(
        "QCcompute/process_excel_HTQC_ox_red_byurl_orca",
        views.process_excel_QcCoumpute_HTQC_ox_red_orca,
        name="process_excel_QcCoumpute_HTQC_ox_red_orca",
    ),
    
    
    path(
        "QCcompute/validate_single_point_energy",
        views.validate_HTQC_single_point_energy_api,
        name="validate_single_point_energy",
    ),
    path(
        "QCcompute/validate_binding_energy",
        views.validate_HTQC_binding_energy_api,
        name="validate_binding_energy",
    ),
    path(
        "QCcompute/validate_pka_pkb",
        views.validate_HTQC_pka_pkb_api,
        name="validate_pka_pkb",
    ),
    path(
        "QCcompute/validate_md_system",
        views.validate_MD_system_api,
        name="validate_md_system",
    ),
    
    
    path(
        "QCcompute/manual_mode_qccompute_page",
        views.manual_mode_qccompute_page,
        name="manual_mode_qccompute_page",
    ),
    
    path(
        "QCcompute/manual_mode_qccompute_byurl",
        views.manual_mode_qccompute_byurl,
        name="manual_mode_qccompute_byurl",
    ),
    
    path(
        "QCcompute/manual_mode_qccompute_byurl_energy",
        views.manual_mode_qccompute_byurl_energy,
        name="manual_mode_qccompute_byurl_energy",
    ),
    
    path(
        "MDcompute/upload_excel",
        views.upload_excel_MDCoumpute,
        name="upload_excel_MDCoumpute",
    ),
    
    path(
        "MDcompute/process_excel_MDCoumpute_byurl",
        views.process_excel_MDCoumpute_byurl,
        name="process_excel_MDCoumpute_byurl",
    ),
    
    path(
        "MDcompute/process_excel_MDCoumpute_ORCA_byurl",
        views.process_excel_MDCoumpute_ORCA_byurl,
        name="process_excel_MDCoumpute_ORCA_byurl",
    ),
    
    
    path(
        "api/electrolytes/",
        ElectrolyteListView.as_view(),
        name="electrolyte-list-create",
    ),
    path(
        "api/electrolytes/<int:pk>/",
        ElectrolyteDetailView.as_view(),
        name="electrolyte-detail",
    ),
    path("api/cation/", CationListView.as_view(), name="cation-list-create"),
    path("api/cation/<int:pk>/", CationDetailView.as_view(), name="cation-detail"),
    path("api/anion/", AnionListView.as_view(), name="anion-list-create"),
    path("api/anion/<int:pk>/", AnionDetailView.as_view(), name="anion-detail"),
    path("api/cation/", CationListView.as_view(), name="cation-list-create"),
    path("api/cation/<int:pk>/", CationDetailView.as_view(), name="cation-detail"),
    path(
        "api/metal_anion/",
        Metal_Anion_EnergyListView.as_view(),
        name="metal_anion-list-create",
    ),
    path(
        "api/metal_anion/<int:pk>/",
        Metal_Anion_EnergyDetailView.as_view(),
        name="metal_anion-detail",
    ),
    path(
        "api/li_electrolyte/",
        Li_ElectrolyteListView.as_view(),
        name="li_electrolyte-list-create",
    ),
    path(
        "api/li_electrolyte/<int:pk>/",
        Li_ElectrolyteDetailView.as_view(),
        name="li_electrolyte-detail",
    ),
    
    path(
        "from_smiles_get_name_page",
        views.from_smiles_get_name_page,
        name="from_smiles_get_name",
    ),  
    path(
        "process_upload_smiles_file/",
        views.process_excel_smiles_query_byurl,
        name="process_upload_smiles_file",
    ),  
    path(
        "query_smiles_name/", views.query_smiles_name, name="query_smiles_name"
    ),  
    
    path(
        "draw_ESP_page/", views.draw_ESP_page_view, name="draw_ESP_page"
    ),  
    path(
        "draw_ESP_func/", views.draw_ESP_view, name="draw_ESP"
    ),  
    path(
        "draw_ESP_func_gbw/", views.draw_ESP_view_gbw, name="draw_ESP_gbw"
    ),  
    
    path(
        "draw_HOMO_LUMO_orb_page/",
        views.draw_HOMO_LUMO_orb_page_view,
        name="draw_HOMO_LUMO_orb_page",
    ),  
    path(
        "draw_HOMO_LUMO_orb_func/",
        views.draw_HOMO_LUMO_orb_remote_view,
        name="draw_HOMO_LUMO_orb",
    ),  
    
    path(
        "NCI_analysis_page/", views.NCI_analysis_page_view, name="NCI_analysis_page"
    ),  
    path(
        "NCI_analysis_func/", views.NCI_analysis_view, name="NCI_analysis"
    ),  
    path(
        "NCI_analysis_promolecular_func/",
        views.NCI_promolecular_analysis_view,
        name="NCI_analysis_promolecular",
    ),  
    
    path("api/", include("autocompute.api_urls")),
]



urlpatterns.append(
    re_path(rf"^(?!{SPA_CATCHALL_PATTERN}).*$", views.spa_index, name="spa_catchall"),
)

