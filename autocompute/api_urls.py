from django.urls import path
from . import api_views

app_name="autocompute"

urlpatterns = [
    path("permissions/", api_views.current_user_permissions_api, name="api_permissions",),
    
    path("molecule_property_similarity_search/", api_views.molecule_property_similarity_search_api, name="api_molecule_property_similarity_search",),
    
    path("material_recommendation_search/", api_views.material_recommendation_search_api, name="api_material_recommendation_search",),
    
    path("mdcompute/", api_views.process_excel_MDCoumpute_byurl_api, name="api_mdcompute",),
    
    path("markov_gdynet/", api_views.submit_markov_gdynet_analysis_api, name="api_markov_gdynet",),
    
    path("single_point_energy_gaussian/", api_views.process_excel_QcCoumpute_HTQC_single_point_energy_byurl_api, name="api_single_point_energy_gaussian",),
    path("binding_energy_gaussian/", api_views.process_excel_QcCoumpute_HTQC_binding_energy_byurl_api, name="api_binding_energy_gaussian",),
    path("pka_pkb_gaussian/", api_views.process_excel_QcCoumpute_HTQC_pka_pkb_api, name="api_pka_pkb_gaussian",),
    path("ox_red_gaussian/", api_views.process_excel_QcCoumpute_HTQC_ox_red_api, name="api_ox_red_gaussian",),
    path("reaction_thermo_gaussian/", api_views.process_excel_HTQC_reaction_thermo_api, name="api_reaction_thermo_gaussian",),
    path("reaction_properties_gaussian/", api_views.process_excel_HTQC_global_reaction_properties_api, name="api_reaction_properties_gaussian",),
    
    path("single_point_energy_orca/", api_views.process_excel_QcCoumpute_HTQC_single_point_energy_byurl_orca_api, name="api_single_point_energy_orca",),
    path("binding_energy_orca/", api_views.process_excel_QcCoumpute_HTQC_binding_energy_byurl_orca_api, name="api_binding_energy_orca",),
    path("ox_red_orca/", api_views.process_excel_QcCoumpute_HTQC_ox_red_orca_api, name="api_ox_red_orca",),
    
    path("query_smiles_to_name/", api_views.process_excel_smiles_query_byurl_api, name="api_query_smiles_to_name",),
    
    path("draw_esp_gaussian/", api_views.draw_ESP_api, name="api_draw_esp_gaussian",),
    path("draw_esp_orca/", api_views.draw_ESP_gbw_api, name="api_draw_esp_orca",),
    path("draw_homo_lumo/", api_views.draw_HOMO_LUMO_orb_api, name="api_draw_homo_lumo",),
    path("nci_scf/", api_views.NCI_analysis_api, name="api_nci_scf",),
    path("nci_promolecular/", api_views.NCI_promolecular_analysis_api, name="api_nci_promolecular",),
]
